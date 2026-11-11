"""Liga inventada para probar la portada sin tocar la API."""
import json
from datetime import datetime, timedelta
from pathlib import Path

TEAMS = [("Los Galácticos de Pepe", "Pepe"), ("Real Sofá CF", "Lucía"), ("Atlético Resaca", "Dani"),
         ("Rayo Vayacansancio", "Marta"), ("Manu United", "Manu")]
# id, nombre, pos, club, valor, puntos temporada, media, puntos jornada 12
PLAYERS = [
    (1, "Mbappé", "DEL", "Real Madrid", 52_000_000, 96, 8.0, 14),
    (2, "Lamine Yamal", "DEL", "FC Barcelona", 48_000_000, 88, 7.3, 11),
    (3, "Pedri", "MED", "FC Barcelona", 31_000_000, 70, 5.8, 6),
    (4, "Vinícius", "DEL", "Real Madrid", 40_000_000, 74, 6.2, 2),
    (5, "Griezmann", "DEL", "Atlético de Madrid", 22_000_000, 65, 5.4, 9),
    (6, "Nico Williams", "DEL", "Athletic Club", 19_500_000, 58, 4.8, 5),
    (7, "Oyarzabal", "DEL", "Real Sociedad", 13_000_000, 61, 5.1, 13),
    (8, "Budimir", "DEL", "Osasuna", 8_400_000, 55, 4.6, 1),
    (9, "Isco", "MED", "Real Betis", 7_000_000, 49, 4.1, 7),
    (10, "Kubo", "MED", "Real Sociedad", 15_000_000, 52, 4.3, 10),
    (11, "Fermín", "MED", "FC Barcelona", 6_900_000, 40, 3.3, 8),
    (12, "Sørloth", "DEL", "Atlético de Madrid", 12_000_000, 47, 3.9, 0),
]
SQUADS = {"0": [7, 8, 6], "1": [9, 4], "2": [5, 12], "3": [10, 3], "4": [2, 11, 1]}
MATCHES = [("Real Madrid", "Osasuna", 3, 0, [1, 4, 8]), ("FC Barcelona", "Real Sociedad", 3, 3, [2, 7, 10, 3, 11]),
           ("Atlético de Madrid", "Real Betis", 2, 1, [5, 9, 12]), ("Athletic Club", "Sevilla FC", 1, 1, [6])]


def make_demo(out="demo_data"):
    d = Path(out)
    (d / "snapshots").mkdir(parents=True, exist_ok=True)
    today = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    info = {p[0]: p for p in PLAYERS}

    pts = [548, 506, 503, 471, 455]
    prev_pts = [487, 468, 448, 410, 433]
    week_pts = [61, 38, 55, 61, 22]

    def snap(day, points, wk):
        st = [{"team_id": str(i), "team": TEAMS[i][0], "manager": TEAMS[i][0], "points": points[i],
               "week_points": wk[i] if wk else None} for i in range(len(TEAMS))]
        st.sort(key=lambda t: -t["points"])
        for p, t in enumerate(st, 1):
            t["position"] = p
        squads = {k: [{"id": str(i), "name": info[i][1]} for i in v] for k, v in SQUADS.items()}
        return {"date": day.strftime("%Y-%m-%d"), "league_id": "demo", "league_name": "Liga de los de siempre",
                "week": 13, "points_week": 12 if wk else None, "standing": st, "squads": squads,
                "jornada": {"week": 12, "matches": [
                    {"id": str(n), "local": l, "visitor": v, "ls": ls, "vs": vs, "date": None,
                     "players": sorted([{"id": str(i), "name": info[i][1], "points": info[i][7], "club": info[i][3]}
                                        for i in ids], key=lambda p: -p["points"])}
                    for n, (l, v, ls, vs, ids) in enumerate(MATCHES)]} if wk else None}

    (d / "snapshots" / f"{today - timedelta(days=1):%Y-%m-%d}.json").write_text(
        json.dumps(snap(today - timedelta(days=1), prev_pts, None), ensure_ascii=False), "utf-8")
    (d / "snapshots" / f"{today:%Y-%m-%d}.json").write_text(
        json.dumps(snap(today, pts, week_pts), ensure_ascii=False), "utf-8")

    players = {str(p[0]): {"name": p[1], "pos": p[2], "club": p[3], "value": p[4], "points": p[5],
                           "avg": p[6], "weeks": {"12": p[7]}} for p in PLAYERS}
    (d / "players.json").write_text(json.dumps(players, ensure_ascii=False), "utf-8")

    acts = [
        ("clausulazo", "Manu United", "Atlético Resaca", 2, 61_500_000, 0.3),
        ("fichaje", "Los Galácticos de Pepe", None, 7, 17_900_000, 1.2),
        ("venta", "Real Sofá CF", None, 9, 6_100_000, 2.5),
        ("compra", "Rayo Vayacansancio", "Real Sofá CF", 10, 14_000_000, 3.4),
        ("fichaje", "Manu United", None, 11, 7_300_000, 4.0),
        ("fichaje", "Los Galácticos de Pepe", None, 6, 22_400_000, 6.1),
    ]
    activity = [{"id": str(n), "type": t, "who": w, "other": o, "player": info[pid][1], "player_id": str(pid),
                 "amount": a, "date": (today - timedelta(days=ago)).isoformat()}
                for n, (t, w, o, pid, a, ago) in enumerate(acts)]
    (d / "activity.json").write_text(json.dumps(activity, ensure_ascii=False, indent=1), "utf-8")
