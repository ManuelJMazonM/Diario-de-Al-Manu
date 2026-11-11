"""Descarga una 'foto' diaria de la liga y acumula el historial de movimientos."""
import json
from datetime import datetime, timezone
from pathlib import Path

from .api import FantasyClient, unwrap

ACTIVITY_TYPES = {
    1: "compra", 4: "blindaje", 6: "premio_jornada", 7: "alineacion_incorrecta",
    9: "nuevo_miembro", 31: "fichaje", 32: "clausulazo", 33: "venta",
}
POSITIONS = {1: "POR", 2: "DEF", 3: "MED", 4: "DEL", 5: "ENT"}


def _pos(x):
    try:
        return POSITIONS.get(int(x))
    except (TypeError, ValueError):
        return None


def _first(*vals):
    for v in vals:
        if v not in (None, ""):
            return v
    return None


def norm_standing(entries):
    out = []
    for i, e in enumerate(entries):
        team = e.get("team") or {}
        mgr = team.get("manager") or {}
        manager = e.get("manager") if isinstance(e.get("manager"), str) else mgr.get("managerName")
        out.append({
            "team_id": str(_first(team.get("id"), e.get("id"))),
            "team": _first(team.get("name"), e.get("name"), manager),
            "manager": manager,
            "points": _first(e.get("points"), team.get("teamPoints"), team.get("points"), 0),
            "week_points": _first(e.get("weekPoints"), team.get("weekPoints")),
            "value": _first(e.get("teamValue"), team.get("teamValue")),
            "position": _first(e.get("position"), i + 1),
            "prev_position": e.get("previousPosition"),
        })
    out.sort(key=lambda t: t["position"])
    return out


def norm_player(p):
    pm = p.get("playerMaster") or p.get("player") or p
    return {
        "id": str(_first(pm.get("id"), p.get("playerMasterId"))),
        "name": _first(pm.get("nickname"), pm.get("name"), p.get("playerName")),
        "pos": _pos(_first(pm.get("positionId"), p.get("positionId"))),
        "value": _first(pm.get("marketValue"), p.get("marketValue")),
        "points": _first(pm.get("points"), p.get("points")),
        "clause": _first(p.get("buyoutClause"), (p.get("playerTeam") or {}).get("buyoutClause")),
    }


def norm_squad(team_resp):
    for path in (("players",), ("playerTeams",), ("data", "players"), ("data",)):
        node = team_resp
        for k in path:
            node = node.get(k) if isinstance(node, dict) else None
        if isinstance(node, list):
            return [norm_player(p) for p in node]
    return []


def norm_activity(a, managers, players):
    pid = _first(a.get("playerMasterId"), a.get("playerId"), (a.get("playerMaster") or {}).get("id"))
    pm = a.get("playerMaster") or a.get("player") or {}
    name = lambda n, i: _first(a.get(f"user{n}Name"), managers.get(str(i)) if i else None)
    return {
        "id": str(_first(a.get("id"), f"{a.get('createdAt')}-{a.get('activityTypeId')}-{pid}")),
        "type": ACTIVITY_TYPES.get(a.get("activityTypeId"), f"tipo_{a.get('activityTypeId')}"),
        "date": _first(a.get("createdAt"), a.get("timestamp"), a.get("publicationDate")),
        # OJO: user1 = quien hace la acción, user2 = la otra parte (verificar con tu liga)
        "who": name(1, a.get("user1Id")),
        "other": name(2, a.get("user2Id")),
        "player": _first(pm.get("nickname"), pm.get("name"), a.get("playerName"),
                         players.get(str(pid)) if pid else None),
        "player_id": str(pid) if pid else None,
        "amount": a.get("amount"),
    }


def norm_clubs(entries):
    """teams-master -> {id: {'name', 'short'}}"""
    out = {}
    for t in entries:
        if t.get("id") is not None:
            out[str(t["id"])] = {"name": _first(t.get("name"), t.get("shortName")),
                                 "short": _first(t.get("shortName"), t.get("name"))}
    return out


def club_name(obj, clubs, key_id="teamId"):
    team = obj.get("team") if isinstance(obj.get("team"), dict) else {}
    cid = _first(obj.get(key_id), team.get("id"))
    return _first(team.get("name"), (clubs.get(str(cid)) or {}).get("name"))


def norm_player_index(entries, clubs):
    """/players -> {id: datos útiles para los reportajes}"""
    idx = {}
    for p in entries:
        pm = p.get("playerMaster") or p
        pid = pm.get("id")
        if pid is None:
            continue
        stats = pm.get("lastStats") or pm.get("playerStats") or []
        weeks = {}
        if isinstance(stats, list):
            for st in stats:
                if isinstance(st, dict) and st.get("weekNumber") is not None:
                    weeks[str(st["weekNumber"])] = _first(st.get("totalPoints"), st.get("points"), st.get("weekPoints"))
        idx[str(pid)] = {
            "name": _first(pm.get("nickname"), pm.get("name")),
            "pos": _pos(pm.get("positionId")),
            "club": club_name(pm, clubs),
            "value": pm.get("marketValue"),
            "points": pm.get("points"),
            "avg": pm.get("averagePoints"),
            "status": pm.get("playerStatus"),
            "weeks": weeks,
        }
    return idx


def norm_matches(calendar, stats, clubs):
    """Une calendario (resultados) y stats (puntos por jugador) de una jornada."""
    by_id = {}
    for m in calendar:
        loc = m.get("local") if isinstance(m.get("local"), dict) else {}
        vis = m.get("visitor") if isinstance(m.get("visitor"), dict) else {}
        lid, vid = _first(m.get("localId"), loc.get("id")), _first(m.get("visitorId"), vis.get("id"))
        by_id[str(m.get("id"))] = {
            "id": str(m.get("id")), "date": _first(m.get("matchDate"), m.get("date")),
            "local": _first(loc.get("name"), (clubs.get(str(lid)) or {}).get("name"), f"Equipo {lid}"),
            "visitor": _first(vis.get("name"), (clubs.get(str(vid)) or {}).get("name"), f"Equipo {vid}"),
            "ls": m.get("localScore"), "vs": m.get("visitorScore"), "state": m.get("matchState"),
            "players": [],
        }
    for m in stats:
        mid = str(_first(m.get("id"), m.get("matchId")))
        match = by_id.setdefault(mid, {"id": mid, "local": None, "visitor": None, "ls": None,
                                        "vs": None, "players": []})
        for side, key in (("local", "local"), ("visitor", "visitor")):
            team = m.get(key) or m.get("home" if key == "local" else "away") or {}
            for pl in team.get("players") or []:
                pts = _first(pl.get("weekPoints"), pl.get("points"))
                if pts is None:
                    continue
                match["players"].append({"id": str(pl.get("id")), "name": _first(pl.get("nickname"), pl.get("name")),
                                         "points": pts, "club": match.get(side)})
        match["players"].sort(key=lambda x: -(x["points"] or 0))
    return list(by_id.values())


def collect(league_id=None, tokens="tokens.json", data_dir="data", max_pages=8, raw=False):
    c = FantasyClient(tokens)
    data = Path(data_dir)
    (data / "snapshots").mkdir(parents=True, exist_ok=True)

    if not league_id:
        leagues = c.leagues()
        if not leagues:
            raise SystemExit("No encuentro ligas en tu cuenta.")
        if len(leagues) > 1:
            print("Tienes varias ligas, pon LEAGUE_ID en config.json:")
            for l in leagues:
                print(f"  {l.get('id')}: {l.get('name')}")
        league_id = leagues[0]["id"]
        league_name = leagues[0].get("name")
    else:
        league_name = None

    standing_raw = c.standing(league_id)
    standing = norm_standing(standing_raw)
    managers = {}
    for e in standing_raw:
        mgr = (e.get("team") or {}).get("manager") or {}
        if mgr.get("id"):
            managers[str(mgr["id"])] = mgr.get("managerName")

    try:
        clubs = norm_clubs(c.teams_master())
    except Exception as e:
        print(f"  aviso: no pude leer los equipos de LaLiga: {e}")
        clubs = {}
    players_raw = c.players()
    player_index = norm_player_index(players_raw, clubs)
    players = {k: v["name"] for k, v in player_index.items()}
    (data / "players.json").write_text(json.dumps(player_index, ensure_ascii=False), "utf-8")

    squads = {}
    for t in standing:
        try:
            squads[t["team_id"]] = norm_squad(c.team(league_id, t["team_id"]))
        except Exception as e:  # una plantilla que falla no tumba la edición
            print(f"  aviso: no pude leer la plantilla de {t['team']}: {e}")

    # Actividad: paginamos hasta topar con movimientos que ya tenemos.
    act_file = data / "activity.json"
    known = {a["id"]: a for a in json.loads(act_file.read_text("utf-8"))} if act_file.exists() else {}
    for page in range(max_pages):
        items = c.activity(league_id, page)
        if not items:
            break
        fresh = [norm_activity(a, managers, players) for a in items]
        new = [a for a in fresh if a["id"] not in known]
        for a in fresh:
            known[a["id"]] = a
        if not new:
            break
    activity = sorted(known.values(), key=lambda a: a["date"] or "", reverse=True)
    act_file.write_text(json.dumps(activity, ensure_ascii=False, indent=1), "utf-8")

    week = c.current_week() or {}
    week_no = _first(week.get("weekNumber"), week.get("number")) if isinstance(week, dict) else None

    # Puntos por jornada: la actual si ya se ha jugado algo, si no la anterior.
    pts_week, raw_week = None, None
    if week_no:
        for w in (week_no, week_no - 1):
            try:
                rows = c.standing_week(league_id, w)
            except Exception as e:
                print(f"  aviso: no pude leer la jornada {w}: {e}")
                continue
            by_team = {}
            for e in rows:
                tid = str(_first((e.get("team") or {}).get("id"), e.get("id")))
                by_team[tid] = _first(e.get("points"), (e.get("team") or {}).get("teamPoints"))
            if any(v for v in by_team.values()):
                pts_week, raw_week = w, rows[:1]
                for t in standing:
                    t["week_points"] = by_team.get(t["team_id"], t["week_points"])
                break

    # Partidos y puntos de jugadores de la última jornada con datos.
    jornada, raw_j = None, {}
    jw = pts_week or week_no
    if jw:
        try:
            cal = c.calendar(jw)
        except Exception as e:
            cal = []
            print(f"  aviso: no pude leer el calendario de la jornada {jw}: {e}")
        try:
            st = c.week_stats(jw)
        except Exception as e:
            st = []
            print(f"  aviso: no hay estadísticas de la jornada {jw} todavía ({e})")
        raw_j = {"calendar": cal[:1], "stats": st[:1]}
        jornada = {"week": jw, "matches": norm_matches(cal, st, clubs)}

    snap = {
        "date": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d"),
        "taken_at": datetime.now(timezone.utc).isoformat(),
        "league_id": str(league_id), "league_name": league_name,
        "week": week_no,
        "points_week": pts_week,
        "standing": standing, "squads": squads, "jornada": jornada,
    }
    if raw:
        snap["_raw_standing"] = standing_raw
        snap["_raw_standing_week"] = raw_week
        snap["_raw_jornada"] = raw_j
        snap["_raw_player"] = players_raw[:1]
    out = data / "snapshots" / f"{snap['date']}.json"
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=1), "utf-8")
    print(f"Foto guardada en {out} ({len(standing)} equipos, {len(activity)} movimientos en historial)")
    return out
