"""Convierte las fotos diarias + movimientos en una edición de periódico."""
import json
import os
import random
import re
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

M = lambda x: f"{(x or 0) / 1_000_000:.1f} M€".replace(".", ",")

from .frases import FRASES, ANUNCIOS

HEAD = FRASES


_used = {}


def _fmt(tpl, rng, **kw):
    """Elige una variante de frase: cambia cada día y no se repite dentro de la misma edición."""
    opts = HEAD[tpl]
    if tpl not in _used:
        n = len(opts)
        start = (_used.get("_day", 0) * 7 + sum(map(ord, tpl))) % n   # cada día arranca en otra variante
        rest = [i for i in range(n) if i != start]
        rng.shuffle(rest)
        _used[tpl] = [start] + rest
    order = _used[tpl]
    i = order.pop(0)
    order.append(i)
    return opts[i].format(**kw)


def _num(x):
    """La API mezcla números y textos ("30000000", "5.8"): todo a número o None."""
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return x
    try:
        f = float(str(x).replace(",", "."))
        return int(f) if f.is_integer() else f
    except ValueError:
        return None


def _clean_numbers(cur, activity):
    for v in (cur.get("_players") or {}).values():
        for k in ("value", "points", "avg"):
            v[k] = _num(v.get(k))
        v["weeks"] = {w: _num(p) for w, p in (v.get("weeks") or {}).items()}
    for t in cur.get("standing") or []:
        for k in ("points", "week_points", "position", "prev_position"):
            if k in t:
                t[k] = _num(t[k])
    for m in ((cur.get("jornada") or {}).get("matches") or []):
        m["ls"], m["vs"] = _num(m.get("ls")), _num(m.get("vs"))
        for p in m.get("players") or []:
            p["points"] = _num(p.get("points"))
        m["players"] = [p for p in m.get("players") or [] if p["points"] is not None]
        m["players"].sort(key=lambda p: -p["points"])
    for a in activity:
        a["amount"] = _num(a.get("amount"))


def pts(n):
    return f"{n} punto" if n in (1, -1) else f"{n} puntos"


def _parse(d):
    if not d:
        return None
    try:
        return datetime.fromisoformat(d.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def load(data_dir="data"):
    data = Path(data_dir)
    snaps = sorted((data / "snapshots").glob("*.json"))
    if not snaps:
        raise SystemExit("No hay fotos todavía. Ejecuta primero: python periodico.py collect")
    cur = json.loads(snaps[-1].read_text("utf-8"))
    prev = json.loads(snaps[-2].read_text("utf-8")) if len(snaps) > 1 else None
    act_file = data / "activity.json"
    activity = json.loads(act_file.read_text("utf-8")) if act_file.exists() else []
    pl_file = data / "players.json"
    cur["_players"] = json.loads(pl_file.read_text("utf-8")) if pl_file.exists() else {}
    _clean_numbers(cur, activity)
    if prev:
        _clean_numbers(prev, [])
    return cur, prev, activity


def _apply_alias(cur, prev, activity, alias):
    """Renombra equipos (nombres cortados por la API o motes) en todo el periódico."""
    if not alias:
        return
    fix = lambda n: alias.get(n, n) if n else n
    for snap in (cur, prev):
        for t in (snap or {}).get("standing") or []:
            t["team"], t["manager"] = fix(t["team"]), fix(t["manager"])
    for a in activity:
        a["who"], a["other"] = fix(a.get("who")), fix(a.get("other"))


def _drop_excluded(cur, prev, activity, exclude):
    """Quita equipos que no juegan (por nombre de equipo o de mánager) y renumera posiciones."""
    ex = {s.strip().lower() for s in exclude or []}
    if not ex:
        return cur, prev, activity
    out = lambda name: (name or "").strip().lower() in ex

    def clean(snap):
        if not snap:
            return snap
        st = [dict(t) for t in snap["standing"] if not (out(t["team"]) or out(t["manager"]))]
        for i, t in enumerate(st, 1):
            t["position"] = i
        return {**snap, "standing": st}

    return clean(cur), clean(prev), [a for a in activity if not out(a.get("who"))]


TRANSFER_TYPES = ("fichaje", "compra", "clausulazo", "venta")
VERB = {"fichaje": "ficha a", "compra": "compra a", "clausulazo": "paga la cláusula de", "venta": "vende a"}
POS_LARGO = {"POR": "portero", "DEF": "defensa", "MED": "centrocampista", "DEL": "delantero", "ENT": "entrenador"}


def _player_info(a, P):
    info = P.get(str(a.get("player_id"))) if a.get("player_id") else None
    if not info and a.get("player"):
        info = next((v for v in P.values() if v.get("name") == a["player"]), None)
    return info or {}


def _owners(cur):
    """id de jugador -> nombre del equipo fantasy que lo tiene."""
    team_name = {t["team_id"]: t["team"] for t in cur["standing"]}
    owners = {}
    for tid, squad in (cur.get("squads") or {}).items():
        if tid in team_name:
            for pl in squad:
                owners[str(pl["id"])] = team_name[tid]
    return owners


def transaction_article(a, P, standing, week, rng):
    """Reportaje largo de una operación importante, sin inventar datos."""
    info = _player_info(a, P)
    who, other, player = a["who"] or "Alguien", a.get("other"), a["player"] or "un jugador"
    pos = POS_LARGO.get(info.get("pos"), "")
    desc = ", ".join(x for x in (pos, info.get("club")) if x) or "jugador"
    amount = a["amount"] or 0
    kw = {"who": who, "other": other or "el mercado", "player": player, "amount": M(amount), "desc": desc}
    paras = []

    # 1. La operación
    t = a["type"] if a["type"] in ("clausulazo", "venta") else ("compra" if a["type"] == "compra" and other else "fichaje")
    p1 = _fmt(f"art_{t}", rng, **kw)
    value = info.get("value")
    if value and amount and a["type"] != "venta":
        diff = (amount - value) / value * 100
        key = "art_caro" if diff > 15 else ("art_barato" if diff < -5 else "art_justo")
        p1 += " " + _fmt(key, rng, pct=f"{abs(diff):.0f}", value=M(value))
    elif value and a["type"] == "venta" and (amount - value) / value * 100 > 5:
        p1 += " " + _fmt("art_venta_buena", rng, pct=f"{(amount - value) / value * 100:.0f}", value=M(value))
    paras.append(p1)

    # 2. Rendimiento del jugador
    if info.get("points") is not None:
        p2 = f"{player} suma {pts(info['points'])} esta temporada"
        if info.get("avg"):
            p2 += f" ({info['avg']:.1f} de media)".replace(".", ",")
        wk = (info.get("weeks") or {}).get(str(week)) if week else None
        if wk is not None:
            p2 += f", y en la jornada {week} hizo {pts(wk)}"
            p2 += _fmt("art_forma_buena", rng) if wk >= 8 else (_fmt("art_forma_mala", rng) if wk <= 2 else ".")
        else:
            p2 += "."
        paras.append(p2)

    # 3. Contexto en la clasificación
    t3 = next((t for t in standing if t["team"] == who), None)
    if t3:
        lider = standing[0]
        if t3["position"] == 1:
            p3 = _fmt("art_lider", rng, who=who, points=t3["points"])
        else:
            p3 = _fmt("art_persigue", rng, who=who, pos=t3["position"], points=t3["points"],
                      gap=lider["points"] - t3["points"], leader=lider["team"])
        if a["type"] == "clausulazo" and other:
            p3 += _fmt("art_victima", rng, other=other)
        elif a["type"] == "venta":
            p3 += _fmt("art_venta_extra", rng)
        paras.append(p3)

    paras.append(_fmt({"clausulazo": "cierre_clausulazo", "venta": "cierre_venta"}.get(a["type"], "cierre_fichaje"), rng))
    return {"kind": a["type"], "headline": _fmt(a["type"], rng, **kw), "date": a["date"],
            "dek": " · ".join(x for x in (
                pos.capitalize(), info.get("club"),
                f"Valor de mercado {M(value)}" if value else None,
                f"{pts(info['points'])} esta temporada" if info.get("points") is not None else None) if x)
            or f"{who} {VERB[a['type']]} {player} por {M(amount)}", "body": paras, "amount": amount}


def build_jornada(cur, rng, owners):
    j = cur.get("jornada") or {}
    matches = [m for m in j.get("matches") or [] if m.get("local")]
    if not matches:
        return None
    week = j.get("week")
    played = [m for m in matches if m.get("ls") is not None and m.get("vs") is not None]
    allp = [dict(p, owner=owners.get(p["id"])) for m in matches for p in m["players"]]
    allp.sort(key=lambda p: -(p["points"] or 0))
    owned = [p for p in allp if p["owner"]]

    def match_score(m):
        goals = (m["ls"] or 0) + (m["vs"] or 0)
        top = sum(p["points"] or 0 for p in m["players"][:3])
        mine = sum(1 for p in m["players"] if owners.get(p["id"]))
        return goals * 3 + top + mine * 4

    featured = None
    if played:
        m = max(played, key=match_score)
        star = m["players"][0] if m["players"] else None
        body = [_fmt("partido_goles" if m["ls"] + m["vs"] >= 4 else "partido_normal", rng, **m)]
        if star:
            o = owners.get(star["id"])
            body.append(f"El mejor para el Fantasy fue {star['name']} con {pts(star['points'])}"
                        + (f", y {o} lo tenía en su plantilla." if o else ", que no tiene dueño en la liga: alguien debería mirar el mercado."))
        mine = [p for p in m["players"] if owners.get(p["id"])]
        if mine:
            body.append("De nuestra liga estaban en el campo: " + ", ".join(
                f"{p['name']} ({owners[p['id']]}, {pts(p['points'])})" for p in mine[:5]) + ".")
        featured = {"headline": _fmt("partido", rng, **m), "body": body, "match": m}

    stars = allp[:5]
    story = None
    if stars:
        s0 = stars[0]
        dek = (_fmt("estrella_dek_dueno", rng, owner=s0["owner"]) if s0["owner"]
               else _fmt("estrella_dek_libre", rng))
        story = {"kind": "estrella", "score": 2e7 + (s0["points"] or 0) * 1e6,
                 "headline": _fmt("estrella", rng, player=s0["name"], points=s0["points"], week=week),
                 "dek": dek}
    return {
        "week": week, "featured": featured, "stars": stars,
        "crack": owned[0] if owned else None,
        "paquete": owned[-1] if len(owned) > 1 else None,
        "results": [{k: m[k] for k in ("local", "visitor", "ls", "vs", "date")} for m in matches],
        "story": story,
    }


RIVALES = {"Real Madrid": ["FC Barcelona", "Atlético de Madrid"],
           "FC Barcelona": ["Real Madrid", "RCD Espanyol"],
           "Atlético de Madrid": ["Real Madrid"],
           "Real Betis": ["Sevilla FC"], "Sevilla FC": ["Real Betis"],
           "Athletic Club": ["Real Sociedad"], "Real Sociedad": ["Athletic Club"],
           "Valencia CF": ["Levante UD", "Villarreal CF"]}
APODO_AFICION = {"Real Madrid": "madridista", "FC Barcelona": "culé", "Atlético de Madrid": "colchonero",
                 "Real Betis": "bético", "Sevilla FC": "sevillista", "Athletic Club": "león",
                 "Valencia CF": "valencianista", "Real Sociedad": "txuri-urdin"}


def _club_key(name):
    """'barça', 'Barcelona', 'FC Barcelona' -> 'FC Barcelona' (para cruzar la afición con los resultados)."""
    import unicodedata
    n = "".join(c for c in unicodedata.normalize("NFD", (name or "").lower().replace("ç", "c"))
                if unicodedata.category(c) != "Mn")
    for key, words in (("FC Barcelona", ("barca", "barcelona")), ("Atlético de Madrid", ("atletico", "atleti")),
                       ("Real Madrid", ("madrid",)), ("Real Betis", ("betis",)), ("Sevilla FC", ("sevilla",)),
                       ("Athletic Club", ("athletic",)), ("Real Sociedad", ("sociedad", "la real")),
                       ("Valencia CF", ("valencia",)), ("Villarreal CF", ("villarreal",)),
                       ("RCD Espanyol", ("espanyol",)), ("Levante UD", ("levante",))):
        if any(w in n for w in words):
            return key
    return name


def build_gossip(cur, activity, standing, jornada, owners, P, aficion, today, rng, fresh_jornada=True):
    """Prensa rosa: todo sale de datos reales; lo especulativo va marcado como rumor."""
    F = lambda key, **kw: _fmt(key, rng, **kw)
    items = []
    if not fresh_jornada:  # en un parón, lo de la jornada vieja ya no es noticia
        jornada = dict(jornada or {}, _matches=[], results=[], stars=[])
    teams = [t["team"] for t in standing]
    recent = lambda a, d: (_parse(a.get("date")) or datetime.min) >= today - timedelta(days=d)
    jpts = {}
    for m in ((jornada or {}).get("_matches") or []):
        for p in m["players"]:
            jpts[p["id"]] = p
    week = (jornada or {}).get("week")
    team_id = {t["team"]: t["team_id"] for t in standing}
    squad_of = lambda team: (cur.get("squads") or {}).get(team_id.get(team)) or []
    club_of = lambda pid: _club_key((P.get(str(pid)) or {}).get("club"))
    name_of = lambda pid: (P.get(str(pid)) or {}).get("name")

    # Culebrón / romance: operaciones entre los mismos dos mánagers
    pairs = {}
    for a in activity:
        if a["type"] in ("clausulazo", "compra") and a.get("who") in teams and a.get("other") in teams and recent(a, 45):
            pairs.setdefault(tuple(sorted((a["who"], a["other"]))), []).append(a)
    for (x, y), ops in sorted(pairs.items(), key=lambda kv: -len(kv[1]))[:1]:
        claus = [o for o in ops if o["type"] == "clausulazo"]
        if claus:
            c = claus[0]
            items.append({"kicker": "Culebrón", "headline": F("g_culebron_t", x=x, y=y),
                          "text": F("g_culebron", who=c["who"], other=c["other"], player=c["player"])})
        elif len(ops) >= 2:
            items.append({"kicker": "Romance de mercado", "headline": F("g_romance_t", x=x, y=y),
                          "text": F("g_romance", n=len(ops))})

    # Corazón roto: vendió a un jugador que después revienta la jornada
    for a in activity:
        if a["type"] == "venta" and a.get("who") in teams and recent(a, 21):
            p = jpts.get(str(a.get("player_id")))
            o = owners.get(p["id"]) if p else None
            if p and (p["points"] or 0) >= 8 and o != a["who"]:
                items.append({"kicker": "Corazón roto",
                              "headline": F("g_corazon_t", who=a["who"], player=a["player"], points=pts(p["points"])),
                              "text": F("g_corazon", amount=M(a["amount"]), week=week,
                                        donde=(f"… con la camiseta de {o}." if o else ". Y encima sigue libre en el mercado."))})
                break

    # Fichaje fantasma: compró caro hace poco y no puntuó
    for a in activity:
        if a["type"] in ("fichaje", "compra", "clausulazo") and a.get("who") in teams and recent(a, 14) \
                and (a.get("amount") or 0) >= 8_000_000:
            p = jpts.get(str(a.get("player_id")))
            if p and (p["points"] or 0) <= 1 and owners.get(p["id"]) == a["who"]:
                items.append({"kicker": "Fichaje fantasma",
                              "headline": F("g_fantasma_t", who=a["who"], player=a["player"], amount=M(a["amount"]),
                                            points=pts(p["points"])),
                              "text": F("g_fantasma", who=a["who"], amount=M(a["amount"]), week=week,
                                        points=pts(p["points"]))})
                break

    # Sucesos: alineaciones indebidas
    for a in activity:
        if a["type"] == "alineacion_incorrecta" and a.get("who") in teams and recent(a, 14):
            items.append({"kicker": "Sucesos", "headline": F("g_sucesos_t", who=a["who"]), "text": F("g_sucesos")})
            break

    # Afición: el equipo del corazón de cada mánager en la jornada real, y las traiciones
    results = {}
    for r in ((jornada or {}).get("results") or []):
        if r.get("ls") is None or r.get("vs") is None:
            continue
        for side, gf, gc, rival in (("local", r["ls"], r["vs"], r["visitor"]), ("visitor", r["vs"], r["ls"], r["local"])):
            results[_club_key(r[side])] = (gf, gc, rival)
    fan_lines = []
    for team, club in (aficion or {}).items():
        if team not in teams:
            continue
        ck = _club_key(club)
        res = results.get(ck)
        if res:
            gf, gc, rival = res
            if gf < gc:
                fan_lines.append({"kicker": "Drama", "headline": F("g_drama_t", team=team),
                                  "text": F("g_drama", club=ck, gf=gf, gc=gc, rival=rival)})
            elif gf > gc + 1:
                fan_lines.append({"kicker": "Euforia", "headline": F("g_euforia_t", team=team, gf=gf, gc=gc, club=ck),
                                  "text": F("g_euforia")})
        traitors = [name_of(pl["id"]) for pl in squad_of(team) if club_of(pl["id"]) in RIVALES.get(ck, [])]
        if traitors:
            fan_lines.append({"kicker": "Traición",
                              "headline": F("g_traicion_t", team=team, apodo=APODO_AFICION.get(ck, f"hincha del {ck}")),
                              "text": F("g_traicion", club=ck, players=", ".join(traitors[:3]))})
    rng.shuffle(fan_lines)
    fan_lines.sort(key=lambda f: f["kicker"] not in ("Drama", "Euforia"))
    seen = set()
    for f in fan_lines:
        if f["kicker"] not in seen and len(seen) < 2:
            items.append(f)
            seen.add(f["kicker"])

    # Coleccionista: 3 o más jugadores del mismo club real
    collectors = []
    for team in teams:
        by_club = {}
        for pl in squad_of(team):
            c = club_of(pl["id"])
            if c:
                by_club.setdefault(c, []).append(name_of(pl["id"]))
        if by_club:
            c, names = max(by_club.items(), key=lambda kv: len(kv[1]))
            if len(names) >= 3:
                collectors.append((len(names), team, c, names))
    if collectors:
        n, team, c, names = max(collectors)
        items.append({"kicker": "Coleccionista", "headline": F("g_coleccion_t", team=team, club=c),
                      "text": F("g_coleccion", n=n, club=c, players=", ".join(names[:4]))})

    # Hucha y rebajas (última semana)
    sold, bought, cheap = {}, {}, {}
    for a in activity:
        if a.get("who") in teams and recent(a, 7) and a.get("amount"):
            if a["type"] == "venta":
                sold[a["who"]] = sold.get(a["who"], 0) + a["amount"]
            elif a["type"] in ("fichaje", "compra", "clausulazo"):
                bought[a["who"]] = bought.get(a["who"], 0) + 1
                if a["amount"] < 3_000_000:
                    cheap[a["who"]] = cheap.get(a["who"], 0) + 1
    savers = [(v, t) for t, v in sold.items() if t not in bought and v >= 10_000_000]
    if savers:
        v, t = max(savers)
        items.append({"kicker": "Economía", "headline": F("g_hucha_t", team=t), "text": F("g_hucha", amount=M(v))})
    if cheap:
        t, n = max(cheap.items(), key=lambda kv: kv[1])
        if n >= 3:
            items.append({"kicker": "Rebajas", "headline": F("g_todoa100_t", team=t), "text": F("g_todoa100", n=n)})

    # Rumor (sin contrastar): la estrella de la jornada que nadie tiene
    free = [p for p in ((jornada or {}).get("stars") or []) if not p.get("owner")]
    if free and teams:
        p = free[0]
        target = rng.choice(teams)
        items.append({"kicker": "Rumor · sin contrastar",
                      "headline": F("g_rumor_t", player=p["name"], target=target),
                      "text": F("g_rumor", player=p["name"], target=target, points=pts(p["points"]), week=week)})

    # Desaparecido
    last = {}
    for a in activity:
        d = _parse(a.get("date"))
        if a.get("who") in teams and d and a["type"] in TRANSFER_TYPES:
            last[a["who"]] = max(last.get(a["who"], d), d)
    idle = sorted(((today - last[t]).days if t in last else 999, t) for t in teams)
    if idle and idle[-1][0] >= 7:
        days, t = idle[-1]
        items.append({"kicker": "Se busca", "headline": F("g_sebusca_t", team=t),
                      "text": F("g_sebusca", dias=(f"Lleva {days} días sin tocar el mercado." if days < 999
                                                   else "No consta que haya fichado nunca."))})

    if not fresh_jornada:  # cotilleo de parón: quién no puede estarse quieto
        moves = {}
        for a in activity:
            if a["type"] in TRANSFER_TYPES and a.get("who") in teams and recent(a, 7):
                moves[a["who"]] = moves.get(a["who"], 0) + 1
        if moves:
            t, n = max(moves.items(), key=lambda kv: kv[1])
            if n >= 2:
                items.insert(0, {"kicker": "Síndrome del parón", "headline": F("g_paron_t", team=t),
                                 "text": F("g_paron", n=n)})

    # Reparto: como mucho 2 cotilleos por equipo y 6 en total, con algo de variedad cada día
    head, tail = items[:2], items[2:]
    rng.shuffle(tail)
    count, picked = {}, []
    for it in head + tail:
        named = [t for t in teams if t in it["headline"] or t in it["text"]]
        if any(count.get(t, 0) >= 2 for t in named):
            continue
        for t in named:
            count[t] = count.get(t, 0) + 1
        picked.append(it)
    return picked[:6]


def thermometer(standing):
    wk = [t for t in standing if t.get("week_points") is not None]
    if len(wk) < 2:
        return None
    hot = max(wk, key=lambda t: t["week_points"])
    cold = min(wk, key=lambda t: t["week_points"])
    return {"hot": {"team": hot["team"], "points": hot["week_points"]},
            "cold": {"team": cold["team"], "points": cold["week_points"]}}


def build_ads(standing, jornada, gossip, top_spender, rng):
    """Anuncios de marcas inventadas (banco en frases.py). Todo ficticio."""
    teams = [t["team"] for t in standing]
    if not teams:
        return []
    j = jornada or {}
    data = {"leader": standing[0]["team"], "last": standing[-1]["team"], "team": rng.choice(teams),
            "spender": top_spender[0] if top_spender else "", "spent": M(top_spender[1]) if top_spender else "",
            "crack": (j.get("crack") or {}).get("name", ""), "crack_owner": (j.get("crack") or {}).get("owner", ""),
            "paquete": (j.get("paquete") or {}).get("name", "")}
    have = {"spender": bool(top_spender), "crack": bool(j.get("crack")), "paquete": bool(j.get("paquete"))}
    out = []
    for ad in ANUNCIOS:
        if ad.get("needs") and not have.get(ad["needs"]):
            continue
        price = f"{rng.choice([9, 12, 14, 19, 24, 29, 39, 49])},99 €"
        try:
            out.append({k: (v.format(price=price, **data) if isinstance(v, str) else v)
                        for k, v in ad.items() if k != "needs"})
        except (KeyError, IndexError):
            continue  # anuncio con una llave que no existe: se ignora
    rng.shuffle(out)
    return out[:8]


GRANDES = ("Real Madrid", "FC Barcelona", "Atlético de Madrid")


def build_paron(cur, jornada, today, aficion):
    """Detecta semanas sin partidos (parón de selecciones) y prepara la próxima jornada."""
    played = [d for d in (_parse(r.get("date")) for r in ((jornada or {}).get("results") or [])) if d]
    last = max(played) if played else None
    nxt = cur.get("next_jornada") or {}
    dates = [d for d in (_parse(m.get("date")) for m in nxt.get("matches") or []) if d]
    first = min(dates) if dates else None
    if not last or (today - last).days < 5:
        return None
    if first and first <= today:
        return None
    fans = {_club_key(c) for c in (aficion or {}).values()}

    def interest(m):
        clubs = {_club_key(m["local"]), _club_key(m["visitor"])}
        return (len(clubs & fans) * 3 + len(clubs & set(GRANDES)) * 2
                + (2 if _club_key(m["visitor"]) in RIVALES.get(_club_key(m["local"]), []) else 0))

    matches = sorted(nxt.get("matches") or [], key=lambda m: m.get("date") or "")
    big = max(matches, key=interest) if matches else None
    return {
        "week": nxt.get("week"), "first_date": first.isoformat() if first else None,
        "days_left": (first.date() - today.date()).days if first else None,
        "days_since": (today - last).days,
        "matches": matches, "big": big,
    }


def build_edition(cur, prev, activity, title="El Diario del Míster", days=7, exclude=None,
                  important_min=10_000_000, max_articles=3, alias=None, aficion=None):
    P = cur.pop("_players", {}) or {}
    _apply_alias(cur, prev, activity, alias or {})
    excl = list(exclude or []) + [alias[e] for e in (exclude or []) if alias and e in alias]
    cur, prev, activity = _drop_excluded(cur, prev, activity, excl)
    # Puntos de la última jornada por jugador (por si /players no los trae)
    jw = (cur.get("jornada") or {}).get("week")
    for m in ((cur.get("jornada") or {}).get("matches") or []):
        for pl in m.get("players") or []:
            if pl["id"] in P and jw:
                P[pl["id"]].setdefault("weeks", {}).setdefault(str(jw), pl["points"])
    rng = random.Random(cur["date"])  # mismos titulares si se regenera el mismo día
    _used.clear()
    _used["_day"] = datetime.fromisoformat(cur["date"]).toordinal()
    today = datetime.fromisoformat(cur["date"])
    since = today - timedelta(days=days)
    recent = [a for a in activity if (_parse(a["date"]) or datetime.min) >= since]
    money = [a for a in recent if a["type"] in TRANSFER_TYPES and a.get("amount")]
    owners = _owners(cur)

    # --- clasificación ---
    prev_pos = {t["team_id"]: t["position"] for t in (prev or {}).get("standing", [])}
    if not prev_pos:  # sin foto de ayer: previousPosition de la API (jornada anterior)
        ranked = sorted((t for t in cur["standing"] if t.get("prev_position")), key=lambda t: t["prev_position"])
        prev_pos = {t["team_id"]: i for i, t in enumerate(ranked, 1)}
    standing = [{**t, "delta": (prev_pos[t["team_id"]] - t["position"]) if t["team_id"] in prev_pos else 0}
                for t in cur["standing"]]
    leader = standing[0]
    week = cur.get("points_week") or cur.get("week")

    # --- reportajes de operaciones importantes ---
    weight = {"clausulazo": 3.0, "fichaje": 1.0, "compra": 1.2, "venta": 0.8}
    ranked_ops = sorted(money, key=lambda a: weight[a["type"]] * a["amount"], reverse=True)
    big = [a for a in ranked_ops if a["type"] == "clausulazo" or a["amount"] >= important_min][:max_articles]
    articles = [transaction_article(a, P, standing, jw or week, rng) for a in big]
    big_ids = {a["id"] for a in big}

    # --- jornada ---
    jornada = build_jornada(cur, rng, owners)
    if jornada:
        jornada["_matches"] = (cur.get("jornada") or {}).get("matches") or []
    aficion = {(alias or {}).get(k, k): v for k, v in (aficion or {}).items()}
    paron = build_paron(cur, jornada, today, aficion)
    gossip = build_gossip(cur, activity, standing, jornada, owners, P, aficion, today, rng,
                          fresh_jornada=not paron)
    if jornada:
        jornada.pop("_matches", None)

    # --- breves ---
    stories = []
    for a in ranked_ops:
        if a["id"] in big_ids:
            continue
        kw = {"who": a["who"] or "Alguien", "other": a.get("other") or "el mercado",
              "player": a["player"] or "un jugador", "amount": M(a["amount"])}
        stories.append({"kind": a["type"], "score": weight[a["type"]] * a["amount"],
                        "headline": _fmt(a["type"], rng, **kw), "date": a["date"]})
    prev_leader = (prev or {}).get("standing", [{}])[0].get("team_id") if prev else None
    if prev_leader and prev_leader != leader["team_id"]:
        stories.append({"kind": "nuevo_lider", "score": 9e9, "headline": _fmt("nuevo_lider", rng, team=leader["team"])})
    for t in standing:
        if abs(t["delta"]) >= 1 and len(standing) <= 6 or abs(t["delta"]) >= 2:
            if t["delta"] == 0:
                continue
            k = "subida" if t["delta"] > 0 else "bajada"
            stories.append({"kind": k, "score": abs(t["delta"]) * 4e6,
                            "headline": _fmt(k, rng, team=t["team"], n=abs(t["delta"]), pos=t["position"],
                                              puestos="puesto" if abs(t["delta"]) == 1 else "puestos")})
    if paron and paron.get("big"):
        b = paron["big"]
        stories.append({"kind": "previa", "score": 1.5e7,
                        "headline": f"Cuenta atrás para el {b['local']}-{b['visitor']}, el plato fuerte de la jornada {paron['week']}",
                        "date": b.get("date")})
    stories.sort(key=lambda s: s["score"], reverse=True)

    # --- portada: el reportaje más gordo; si no hay, la estrella de la jornada ---
    if articles:
        lead, features = articles[0], articles[1:]
        if jornada and jornada["story"] and not paron:
            stories.insert(0, jornada["story"])
    elif paron:
        dias = paron["days_left"]
        lead = {"kind": "paron",
                "headline": _fmt("paron_t", rng),
                "dek": (f"La jornada {paron['week']} arranca en {dias} {'día' if dias == 1 else 'días'}"
                        if dias is not None else "La liga vuelve muy pronto"),
                "body": [f"Han pasado {paron['days_since']} días desde el último partido y en la clasificación "
                         f"no se mueve nada: {leader['team']} sigue arriba con {leader['points']} puntos.",
                         _fmt("paron_cuerpo", rng)]}
        features = []
    elif jornada and jornada["story"]:
        lead, features = dict(jornada["story"], body=(jornada["featured"] or {}).get("body", [])), []
    elif stories:
        lead, features = stories.pop(0), []
    else:
        lead, features = {"kind": "lider", "headline": _fmt("lider", rng, team=leader["team"], points=leader["points"])}, []

    spend = {}
    for a in money:
        if a["type"] != "venta":
            spend[a["who"]] = spend.get(a["who"], 0) + a["amount"]
    edition = {
        "title": title, "league": cur.get("league_name"), "date": cur["date"], "week": cur.get("week"),
        "points_week": cur.get("points_week"),
        "lead": lead, "features": features, "briefs": stories[:6], "standing": standing,
        "market": sorted(money, key=lambda a: a["date"] or "", reverse=True)[:12],
        "jornada": jornada, "gossip": gossip, "paron": paron, "thermo": thermometer(standing), "top_spender": max(spend.items(), key=lambda x: x[1]) if spend else None,
        "editorial": None,
    }
    if os.environ.get("ANTHROPIC_API_KEY"):
        for art in [lead] + features:
            if art.get("body") and art.get("kind") in TRANSFER_TYPES:
                art["body"] = llm_article(art) or art["body"]
    edition["ads"] = build_ads(standing, jornada, gossip, edition["top_spender"], rng)
    edition["editorial"] = llm_editorial(edition) or default_editorial(edition, rng)
    return edition


def default_editorial(e, rng):
    F = lambda key, **kw: _fmt(key, rng, **kw)
    st = e["standing"]
    l = st[0]
    gap = l["points"] - st[1]["points"] if len(st) > 1 else 0
    parts = [F("ed_lider", leader=l["team"], points=l["points"], gap=gap)]
    if e["top_spender"]:
        parts.append(F("ed_gasto", who=e["top_spender"][0], amount=M(e["top_spender"][1])))
    j = e.get("jornada")
    if j and j.get("crack") and not e.get("paron"):
        c = j["crack"]
        parts.append(F("ed_crack", player=c["name"], points=pts(c["points"]), owner=c["owner"]))
    parts.append(F("ed_farolillo", team=st[-1]["team"]))
    parts.append(F("ed_cierre"))
    return " ".join(parts)


def _llm(prompt, max_tokens=600):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", method="POST",
        data=json.dumps({"model": os.environ.get("ANTHROPIC_MODEL", "claude-haiku-5-5"),
                         "max_tokens": max_tokens,
                         "messages": [{"role": "user", "content": prompt}]}).encode(),
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["content"][0]["text"].strip()
    except Exception as ex:
        print(f"  aviso: la IA falló ({ex}), uso la plantilla")
        return None


def llm_article(art):
    txt = _llm("Eres redactor de un diario deportivo sensacionalista español que cubre una liga fantasy "
               "entre amigos. Reescribe esta noticia en 3 párrafos cortos (90-140 palabras en total), con "
               "humor y pique sano, sin insultos y SIN inventar ningún dato, cifra ni declaración. "
               "Separa los párrafos con una línea en blanco. Solo el texto, sin titular.\n"
               + json.dumps({k: art[k] for k in ("headline", "dek", "body")}, ensure_ascii=False))
    return [p.strip() for p in txt.split("\n\n") if p.strip()] if txt else None


def llm_editorial(e):
    """Opcional: si hay ANTHROPIC_API_KEY, un editorial con más salsa."""
    facts = {k: e[k] for k in ("lead", "briefs", "standing", "market", "jornada")}
    return _llm("Eres el columnista de un diario deportivo sensacionalista español que cubre una liga "
                "fantasy entre amigos. Escribe un editorial de 120-160 palabras, con humor y pique sano, "
                "sin insultos, usando SOLO estos datos (no inventes cifras):\n"
                + json.dumps(facts, ensure_ascii=False, default=str))


def render(edition, out_dir="site", template=Path(__file__).parent / "periodico.html"):
    out = Path(out_dir)
    (out / "archivo").mkdir(parents=True, exist_ok=True)
    js = json.dumps(edition, ensure_ascii=False).replace("</", "<\\/")
    html = Path(template).read_text("utf-8").replace("/*EDITION*/null", js)
    # Título real en el <head> para pestañas y vistas previas (WhatsApp, Telegram...)
    import html as _h
    titulo = _h.escape(edition["title"])
    html = re.sub(r"<title>.*?</title>", f"<title>{titulo}</title>", html, count=1)
    html = html.replace("<title>", f'<meta property="og:title" content="{titulo}">\n'
                        f'<meta property="og:description" content="{_h.escape(edition["lead"]["headline"])}">\n<title>', 1)
    (out / "index.html").write_text(html, "utf-8")
    (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n", "utf-8")
    (out / "archivo" / f"{edition['date']}.html").write_text(html, "utf-8")
    print(f"Portada generada en {out / 'index.html'}")
