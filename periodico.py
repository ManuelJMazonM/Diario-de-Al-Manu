#!/usr/bin/env python3
"""Uso:
  python periodico.py collect   # descarga la foto de hoy (necesita tokens.json)
  python periodico.py build     # genera site/index.html a partir de las fotos
  python periodico.py daily     # collect + build (lo que pones en el cron)
  python periodico.py login     # inicia sesión (cliente de la app) y crea tokens.json
  python periodico.py diag      # revisa el estado del login sin mostrar los tokens
  python periodico.py demo      # datos inventados para ver la portada sin login
"""
import json
import sys
from pathlib import Path

from lff import news

CFG = json.loads(Path("config.json").read_text("utf-8")) if Path("config.json").exists() else {}


def build(data_dir="data"):
    cur, prev, activity = news.load(data_dir)
    ed = news.build_edition(cur, prev, activity, title=CFG.get("TITLE", "El Diario del Míster"),
                            days=CFG.get("DAYS", 7), exclude=CFG.get("EXCLUDE", []),
                            important_min=CFG.get("IMPORTANT_MIN", 10_000_000),
                            alias=CFG.get("ALIAS", {}), aficion=CFG.get("AFICION", {}))
    news.render(ed, CFG.get("OUT_DIR", "site"))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "daily"
    if cmd in ("collect", "daily"):
        from lff.collect import collect
        collect(CFG.get("LEAGUE_ID"), CFG.get("TOKENS", "tokens.json"), "data", raw="--raw" in sys.argv)
    if cmd in ("build", "daily"):
        build()
    if cmd == "login":
        from lff.login import login
        login(CFG.get("TOKENS", "tokens.json"))
    if cmd == "diag":
        from lff.api import diagnose
        diagnose(CFG.get("TOKENS", "tokens.json"), sys.argv[2] if len(sys.argv) > 2 else None)
    if cmd == "demo":
        from lff.demo import make_demo
        make_demo("demo_data")
        CFG.setdefault("TITLE", "El Diario de Al-Manu")
        CFG.setdefault("AFICION", {"Manu United": "Barça", "Rayo Vayacansancio": "Real Madrid", "Atlético Resaca": "Atleti"})
        build("demo_data")
    if cmd not in ("collect", "build", "daily", "demo", "diag", "login"):
        print(__doc__)


if __name__ == "__main__":
    main()
