"""Login con el cliente de la app móvil (Authorization Code + PKCE).

Mismo flujo que https://github.com/sergioalmela/la-liga-fantasy-analyzer:
inicias sesión en la web de LaLiga, el navegador intenta abrir
authredirect://com.lfp.laligafantasy/?state=...&code=... (y no puede), y tú copias
esa dirección desde la pestaña Network. Tu contraseña nunca pasa por este script.
"""
import base64
import hashlib
import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

from .api import TOKEN_URL, UA

APP_CLIENT_ID = "af88bcff-1157-40a0-b579-030728aacf0b"
REDIRECT = "authredirect://com.lfp.laligafantasy"
POLICY = "B2C_1A_5ULAIP_PARAMETRIZED_SIGNIN"
AUTHORIZE = "https://login.laliga.es/laligadspprob2c.onmicrosoft.com/oauth2/v2.0/authorize"
SCOPE = "openid offline_access"

INSTRUCCIONES = """
1. Se abre el navegador con el login de LaLiga. ANTES de iniciar sesión:
   F12 -> Network -> marca 'Keep log' -> en Filter escribe: confirmed
2. Inicia sesión normalmente. Al terminar la página se quedará en blanco o
   dará error (es normal: intenta abrir la app móvil).
3. Haz clic en la petición 'confirmed' -> Headers -> Response Headers ->
   copia el valor de 'location' (empieza por authredirect://).
4. Pégalo aquí abajo y pulsa Enter.
"""


def _b64(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def login(tokens_path="tokens.json"):
    verifier = _b64(secrets.token_bytes(64))
    state = _b64(secrets.token_bytes(16))
    url = AUTHORIZE + "?" + urllib.parse.urlencode({
        "p": POLICY, "client_id": APP_CLIENT_ID, "response_type": "code",
        "redirect_uri": REDIRECT, "scope": SCOPE,
        "code_challenge": _b64(hashlib.sha256(verifier.encode()).digest()),
        "code_challenge_method": "S256", "state": state, "nonce": state,
    })
    print(INSTRUCCIONES)
    print("Si no se abre solo, copia esta dirección en el navegador:\n" + url + "\n")
    webbrowser.open(url)

    redirect = input("Pega aquí la dirección authredirect://...: ").strip().strip("'\"")
    parsed = urllib.parse.urlparse(redirect)
    params = urllib.parse.parse_qs(parsed.query or parsed.fragment)
    if not redirect.startswith(REDIRECT):
        raise SystemExit("Eso no empieza por authredirect://com.lfp.laligafantasy. Revisa el paso 3.")
    if "error" in params:
        raise SystemExit(f"LaLiga devolvió un error: {params.get('error_description', params['error'])}")
    if params.get("state", [""])[0] != state:
        raise SystemExit("El 'state' no coincide: esa dirección es de otro intento. Repite 'login'.")
    code = params.get("code", [""])[0]
    if not code:
        raise SystemExit("La dirección no trae 'code'.")

    body = urllib.parse.urlencode({
        "grant_type": "authorization_code", "client_id": APP_CLIENT_ID, "scope": SCOPE,
        "code": code, "code_verifier": verifier, "redirect_uri": REDIRECT,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, method="POST", headers={
        "Content-Type": "application/x-www-form-urlencoded", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            tokens = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"No se pudo canjear el código ({e.code}): {e.read()[:300]!r}\n"
                         "El código caduca en pocos minutos: repite 'login' y pégalo enseguida.")
    tokens["client_id"] = APP_CLIENT_ID
    Path(tokens_path).write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    print(f"\nListo: {tokens_path} guardado con el cliente de la app. Prueba: python periodico.py diag")
