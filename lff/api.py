"""Cliente mínimo (solo lectura) de la API no oficial de LaLiga Fantasy, temporada 26/27.

Endpoints y flujo de login tomados de https://github.com/Externoak/LaLigaApp.
Solo usa la librería estándar de Python.
"""
import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HOST = "https://fantasy-api.llt-services.com"
API = f"{HOST}/api"
STATS = f"{HOST}/stats"
COMPETITION = 1  # 1 = LaLiga
CMP = f"/v1/competition/{COMPETITION}"
TOKEN_URL = ("https://login.laliga.es/laligadspprob2c.onmicrosoft.com/oauth2/v2.0/token"
             "?p=B2C_1A_5ULAIP_PARAMETRIZED_SIGNIN")
WEB_CLIENT_ID = "6457fa17-1224-416a-b21a-ee6ce76e9bc0"  # cliente de miliga.laliga.com
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
X_APP = "2"  # la web/app oficial manda esta cabecera


def api_headers(bearer, x_app=True, ua=UA):
    h = {"Authorization": f"Bearer {bearer}", "x-lang": "es", "Accept": "application/json", "User-Agent": ua}
    if x_app:
        h["x-app"] = X_APP
    return h


class AuthError(RuntimeError):
    pass


def _jwt_exp(token):
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload)).get("exp", 0)
    except Exception:
        return 0


class FantasyClient:
    def __init__(self, tokens_path="tokens.json", delay=0.6):
        self.tokens_path = Path(tokens_path)
        if not self.tokens_path.exists():
            raise AuthError(f"No existe {self.tokens_path}. Mira el README: 'Conseguir el token'.")
        self.tokens = json.loads(self.tokens_path.read_text(encoding="utf-8"))
        if "refresh_token" not in self.tokens:
            raise AuthError("tokens.json no tiene refresh_token: copia la respuesta COMPLETA del login.")
        self.delay = delay

    # ---------- auth ----------
    @property
    def bearer(self):
        return self.tokens.get("id_token") or self.tokens.get("access_token")

    def refresh(self):
        body = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"],
            "client_id": self.tokens.get("client_id", WEB_CLIENT_ID),
            "scope": "openid offline_access",
        }).encode()
        req = urllib.request.Request(TOKEN_URL, data=body, method="POST", headers={
            "Content-Type": "application/x-www-form-urlencoded", "User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                new = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise AuthError(f"Fallo al refrescar el token ({e.code}): {e.read()[:300]!r}. "
                            "Vuelve a capturarlo a mano.") from e
        if not (new.get("id_token") or new.get("access_token")):
            raise AuthError("La respuesta del refresh no trae token.")
        self.last_refresh_keys = sorted(new)
        # Si no llega id_token nuevo, el viejo está caducado: no reutilizarlo.
        if not new.get("id_token"):
            self.tokens.pop("id_token", None)
        # B2C rota el refresh_token: hay que guardar SIEMPRE el nuevo.
        self.tokens.update({k: v for k, v in new.items() if v})
        self.tokens_path.write_text(json.dumps(self.tokens, indent=2), encoding="utf-8")

    def _ensure_fresh(self):
        if _jwt_exp(self.bearer or "") < time.time() + 120:
            self.refresh()

    # ---------- http ----------
    def get(self, path, _retry=True):
        self._ensure_fresh()
        sep = "&" if "?" in path else "?"
        url = f"{path if path.startswith('http') else API + path}{sep}x-lang=es"
        req = urllib.request.Request(url, headers=api_headers(self.bearer))
        time.sleep(self.delay)  # no machacar la API
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            if e.code == 401 and _retry:
                self.refresh()
                return self.get(path, _retry=False)
            if e.code == 429 and _retry:
                time.sleep(10)
                return self.get(path, _retry=False)
            raise

    # ---------- endpoints ----------
    def leagues(self):
        return unwrap(self.get(f"{CMP}/leagues"), "leagues")

    def standing(self, league_id):
        return unwrap(self.get(f"{CMP}/leagues/{league_id}/standing"))

    def standing_week(self, league_id, week):
        return unwrap(self.get(f"{CMP}/leagues/{league_id}/standing/{week}"))

    def activity(self, league_id, page=0):
        return unwrap(self.get(f"{CMP}/leagues/{league_id}/activity/{page}"))

    def team(self, league_id, team_id):
        return self.get(f"{CMP}/leagues/{league_id}/teams/{team_id}")

    def players(self):
        return unwrap(self.get(f"{CMP}/players"))

    def calendar(self, week):
        return unwrap(self.get(f"{CMP}/calendar?weekNumber={week}"), "matches")

    def week_stats(self, week):
        return unwrap(self.get(f"{STATS}/v1/competition/{COMPETITION}/stats/week/{week}"), "matches")

    def teams_master(self):
        return unwrap(self.get("/v3/teams-master"), "teams")

    def current_week(self):
        return self.get(f"{CMP}/week/current")


def _claims(token):
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        c = json.loads(base64.urlsafe_b64decode(payload))
        return {k: c.get(k) for k in ("aud", "azp", "tfp", "acr", "scp", "exp")}
    except Exception:
        return "no es un JWT legible"


def diagnose(tokens_path="tokens.json", bearer_file=None):
    """Muestra el estado de los tokens SIN imprimir los tokens."""
    c = FantasyClient(tokens_path)
    if bearer_file:
        return _diag_web_bearer(c, bearer_file)
    now = time.time()
    print("Claves en tokens.json:", sorted(c.tokens))
    for k in ("id_token", "access_token"):
        if c.tokens.get(k):
            cl = _claims(c.tokens[k])
            exp = cl.get("exp", 0) if isinstance(cl, dict) else 0
            print(f"  {k}: {cl}  -> {'CADUCADO' if exp < now else f'vale {int((exp-now)/60)} min'}")
    print("client_id usado para refrescar:", c.tokens.get("client_id", WEB_CLIENT_ID + " (por defecto)"))
    print("\nRefrescando...")
    try:
        c.refresh()
    except AuthError as e:
        print("  FALLO:", e)
        return
    print("  La respuesta trae:", c.last_refresh_keys)
    for k in ("id_token", "access_token"):
        if c.tokens.get(k):
            print(f"  nuevo {k}: {_claims(c.tokens[k])}")
    variants = [
        ("sin x-app, UA propio", dict(x_app=False, ua="periodico-fantasy/1.0")),
        ("con x-app, UA propio", dict(x_app=True, ua="periodico-fantasy/1.0")),
        ("sin x-app, UA navegador", dict(x_app=False)),
        ("con x-app, UA navegador", dict(x_app=True)),
    ]
    for label in ("id_token", "access_token"):
        tok = c.tokens.get(label)
        if not tok:
            continue
        for vname, kw in variants:
            req = urllib.request.Request(f"{API}{CMP}/leagues?x-lang=es", headers=api_headers(tok, **kw))
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    print(f"  /leagues con {label}, {vname}: OK ({r.status})")
            except urllib.error.HTTPError as e:
                body = e.read()[:200].decode("utf-8", "replace").replace("\n", " ")
                print(f"  /leagues con {label}, {vname}: {e.code}  {body}")
            time.sleep(0.5)


def _diag_web_bearer(c, bearer_file):
    """Prueba el token que usa la web oficial (copiado de la cabecera Authorization)."""
    raw = Path(bearer_file).read_text("utf-8").strip()
    tok = raw.split()[-1]  # quita "Bearer " si viene
    print("Token de la web:", _claims(tok), f"(longitud {len(tok)})")
    for k in ("id_token", "access_token"):
        print(f"  ¿es igual al {k} de tokens.json?", tok == c.tokens.get(k))
    req = urllib.request.Request(f"{API}{CMP}/leagues?x-lang=es", headers=api_headers(tok))
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("  /leagues con el token de la web: OK", r.status)
    except urllib.error.HTTPError as e:
        print("  /leagues con el token de la web:", e.code, e.read()[:200].decode("utf-8", "replace"))


def unwrap(resp, *keys):
    """La API devuelve a veces [..], a veces {elements:[..]} o {data:[..]}."""
    if isinstance(resp, list):
        return resp
    if isinstance(resp, dict):
        for k in ("elements", "data", *keys):
            v = resp.get(k)
            if isinstance(v, list):
                return v
            if isinstance(v, dict):
                inner = unwrap(v, *keys)
                if inner:
                    return inner
    return []
