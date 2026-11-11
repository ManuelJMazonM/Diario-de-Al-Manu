"""Convierte las fotos diarias + movimientos en una edición de periódico."""
import json
import os
import random
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

M = lambda x: f"{(x or 0) / 1_000_000:.1f} M€".replace(".", ",")

HEAD = {
    "clausulazo": [
        "¡CLAUSULAZO! {who} le arranca a {player} a {other} por {amount}",
        "Atraco a mano armada: {who} paga la cláusula de {player} ({amount})",
        "{other} no da crédito: {who} se lleva a {player} por la vía rápida",
    ],
    "fichaje": [
        "{who} rompe la hucha: {player} llega por {amount}",
        "Bombazo en el mercado: {player} ficha por {who} ({amount})",
        "{who} se hace con {player} tras una puja de {amount}",
        "{player} ya tiene nuevo jefe: {who} paga {amount}",
        "Movimiento en los despachos: {who} cierra a {player} ({amount})",
        "{who} no se esconde y suelta {amount} por {player}",
    ],
    "compra": [
        "{who} negocia con {other} y se queda a {player} por {amount}",
        "Acuerdo cerrado: {player} cambia de manos de {other} a {who}",
    ],
    "venta": [
        "{who} hace caja: vende a {player} por {amount}",
        "Adiós, {player}: {who} lo vende y se embolsa {amount}",
    ],
    "lider": [
        "{team} sigue mandando: líder con {points} puntos",
        "Nadie tose a {team}, que lidera con {points} puntos",
    ],
    "nuevo_lider": [
        "¡CAMBIO EN LO MÁS ALTO! {team} es el nuevo líder",
        "Golpe de estado: {team} asalta el liderato",
    ],
    "subida": ["{team} se dispara: sube {n} {puestos} y ya es {pos}º", "{team} escala {n} {puestos}: ya es {pos}º"],
    "bajada": ["Crisis en {team}: cae {n} {puestos} hasta el {pos}º", "{team} se desinfla y baja al {pos}º puesto"],
    "estrella": [
        "{player} arrasa: {points} puntos en la jornada {week}",
        "Exhibición de {player}: {points} puntos y la jornada a sus pies",
        "{player} se sale con {points} puntos",
    ],
    "partido": [
        "{local} {ls}-{vs} {visitor}: el partido que movió la liga",
        "Lo que pasó en el {local}-{visitor} ({ls}-{vs})",
    ],
    "quieto": ["{who} lleva {days} días sin tocar el mercado. ¿Sigue vivo?"],
}


_used = {}


def _fmt(tpl, rng, **kw):
    # Va rotando las plantillas para no repetir el mismo titular seguido.
    opts = HEAD[tpl]
    if tpl not in _used:
        _used[tpl] = rng.sample(range(len(opts)), len(opts))
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
    club = (", " if pos else "") + info["club"] if info.get("club") else ""
    if not pos and not club:
        pos = "jugador"
    amount = a["amount"] or 0
    paras = []

    # 1. La operación
    if a["type"] == "clausulazo":
        p1 = f"{who} no ha pedido permiso: ha pagado {M(amount)} por la cláusula de {player} ({pos}{club})"
        p1 += f", y se lo ha arrebatado a {other}." if other else "."
    elif a["type"] == "venta":
        p1 = f"{who} ha decidido hacer caja con {player} ({pos}{club}), y se embolsa {M(amount)}."
    elif a["type"] == "compra" and other:
        p1 = f"{who} y {other} han cerrado un acuerdo: {player} ({pos}{club}) cambia de manos por {M(amount)}."
    else:
        p1 = f"{who} ha ganado la puja por {player} ({pos}{club}) con una oferta de {M(amount)}."
    value = info.get("value")
    if value and amount and a["type"] != "venta":
        diff = (amount - value) / value * 100
        if diff > 15:
            p1 += f" Ha pagado un {diff:.0f}% por encima de su valor de mercado ({M(value)}): o sabe algo, o se ha dejado llevar."
        elif diff < -5:
            p1 += f" Y a buen precio: un {-diff:.0f}% por debajo de su valor de mercado ({M(value)})."
        else:
            p1 += f" Un precio en línea con su valor de mercado ({M(value)})."
    elif value and a["type"] == "venta":
        diff = (amount - value) / value * 100
        if diff > 5:
            p1 += f" Lo vende un {diff:.0f}% por encima de su valor ({M(value)}): buen negocio."
    paras.append(p1)

    # 2. Rendimiento del jugador
    if info.get("points") is not None:
        p2 = f"{player} suma {pts(info['points'])} esta temporada"
        if info.get("avg"):
            p2 += f" ({info['avg']:.1f} de media)".replace(".", ",")
        wk = (info.get("weeks") or {}).get(str(week)) if week else None
        if wk is not None:
            p2 += f", y en la jornada {week} hizo {pts(wk)}"
            p2 += ": llega en plena forma." if wk >= 8 else (". Toca esperar a que despierte." if wk <= 2 else ".")
        else:
            p2 += "."
        paras.append(p2)

    # 3. Contexto en la clasificación
    by_team = {t["team"]: t for t in standing}
    t = by_team.get(who)
    if t:
        lider = standing[0]
        if t["position"] == 1:
            p3 = f"{who} es líder con {t['points']} puntos y no quiere que nadie se le acerque."
        else:
            p3 = (f"{who} es {t['position']}º con {t['points']} puntos, a {lider['points'] - t['points']} "
                  f"del liderato de {lider['team']}.")
        if a["type"] == "clausulazo" and other:
            p3 += f" {other} pierde a una pieza importante y tendrá que reaccionar en el mercado."
        elif a["type"] == "venta":
            p3 += " Habrá que ver en qué invierte el dinero."
        paras.append(p3)

    opts = {
        "venta": ["Seguiremos informando.", "El dinero ya quema en la cuenta.",
                  "Ahora toca acertar con el siguiente fichaje."],
        "clausulazo": ["La respuesta de la víctima no se hará esperar.", "El vestuario ya comenta la jugada.",
                       "Ahora le toca demostrar que valía la cláusula."],
    }.get(a["type"], ["El vestuario ya comenta la jugada.", "Seguiremos informando.",
                      "Ahora le toca demostrarlo en el campo."])
    fresh = [o for o in opts if o not in _used.setdefault("_cierres", [])] or opts
    cierre = rng.choice(fresh)
    _used["_cierres"].append(cierre)
    paras.append(cierre)
    kw = {"who": who, "other": other or "el mercado", "player": player, "amount": M(amount)}
    return {"kind": a["type"], "headline": _fmt(a["type"], rng, **kw), "date": a["date"],
            "dek": " · ".join(x for x in (
                POS_LARGO.get(info.get("pos"), "").capitalize(), info.get("club"),
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
        body = [f"{m['local']} y {m['visitor']} firmaron un {m['ls']}-{m['vs']}"
                + (" en un partido de ida y vuelta." if m["ls"] + m["vs"] >= 4 else ".")]
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
        dek = (f"{s0['owner']} lo tiene en su equipo y se frota las manos." if s0["owner"]
               else "Y nadie de la liga lo tiene en su plantilla.")
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


def build_edition(cur, prev, activity, title="El Diario del Míster", days=7, exclude=None,
                  important_min=10_000_000, max_articles=3, alias=None):
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
    stories.sort(key=lambda s: s["score"], reverse=True)

    # --- portada: el reportaje más gordo; si no hay, la estrella de la jornada ---
    if articles:
        lead, features = articles[0], articles[1:]
        if jornada and jornada["story"]:
            stories.insert(0, jornada["story"])
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
        "jornada": jornada, "top_spender": max(spend.items(), key=lambda x: x[1]) if spend else None,
        "editorial": None,
    }
    if os.environ.get("ANTHROPIC_API_KEY"):
        for art in [lead] + features:
            if art.get("body") and art.get("kind") in TRANSFER_TYPES:
                art["body"] = llm_article(art) or art["body"]
    edition["editorial"] = llm_editorial(edition) or default_editorial(edition, rng)
    return edition


def default_editorial(e, rng):
    st = e["standing"]
    l = st[0]
    gap = l["points"] - st[1]["points"] if len(st) > 1 else 0
    s = f"{l['team']} manda con {l['points']} puntos y {gap} de ventaja sobre el segundo. "
    if e["top_spender"]:
        s += f"En los despachos, {e['top_spender'][0]} es quien más ha tirado de cartera ({M(e['top_spender'][1])}). "
    j = e.get("jornada")
    if j and j.get("crack"):
        c = j["crack"]
        s += f"En el césped, {c['name']} ({pts(c['points'])}) fue lo mejor para {c['owner']}. "
    s += f"Mientras, {st[-1]['team']} sigue buscando el camino desde el fondo. "
    s += rng.choice(["La liga huele a pólvora.", "Se avecinan curvas.", "Aquí no se rinde nadie."])
    return s


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
    (out / "index.html").write_text(html, "utf-8")
    (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n", "utf-8")
    (out / "archivo" / f"{edition['date']}.html").write_text(html, "utf-8")
    print(f"Portada generada en {out / 'index.html'}")
