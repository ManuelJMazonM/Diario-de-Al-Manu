# El Diario del Míster

Periódico deportivo diario de tu liga privada de **LaLiga Fantasy**: fichajes, clausulazos,
ventas, subidas y bajadas en la clasificación, el que más gasta y el que lleva semanas sin mover ficha.

Solo usa la librería estándar de Python 3.10+. Sin dependencias.

```
python periodico.py demo      # portada con una liga inventada (no necesita login)
python periodico.py collect   # descarga la foto de hoy
python periodico.py build     # genera site/index.html
python periodico.py daily     # las dos cosas (para el cron)
```

## 1. Iniciar sesión (una sola vez, dura ~90 días)

La API solo acepta tokens del cliente de la app móvil, así que no sirven los tokens
que se sacan de la web. El script hace el mismo login que la app (PKCE):

```
python periodico.py login
```

1. Se abre el login de LaLiga. **Antes de entrar:** F12 → Network → marca **Keep log** →
   en Filter escribe `confirmed` (email y contraseña) o `authresp` (cuenta de Google).
2. Inicia sesión. Al final la página se queda cargando o en blanco: es normal.
3. Clic en esa petición → Headers → Response Headers → copia `location`
   (empieza por `authredirect://`) y pégalo en la terminal **enseguida**.
4. Comprueba con `python periodico.py diag`: tiene que salir `OK`.

Tu contraseña nunca pasa por el script. A partir de ahí el token se renueva solo.
Si un día falla con `AuthError` o 401, repite `login`.

## 2. Configurar

```
cp config.example.json config.json
python periodico.py collect --raw
```

Si tienes varias ligas, el primer `collect` te las lista: pon el id en `LEAGUE_ID`.
`--raw` guarda también la respuesta en bruto de la clasificación dentro de la foto, útil para
comprobar campos la primera vez.

**Cosas a verificar con tu liga real** (la API no está documentada):
- En `activity`, el script asume `user1` = quien hace la acción y `user2` = la otra parte.
  Si en los clausulazos sale al revés, cámbialo en `lff/collect.py → norm_activity`.
- Las noticias de "sube/baja puestos" necesitan al menos dos fotos (dos días).

## 3. Automatizarlo en GitHub

El workflow `.github/workflows/periodico.yml` genera la edición cada mañana y la publica
en la rama `gh-pages` (Settings → Pages → Deploy from a branch → gh-pages / root).
No usa acciones externas: solo git, python3 y gh. El repo debe ser **privado** (Pages desde un repo privado requiere
GitHub Pro, gratis con el Student Pack). La web publicada es accesible para quien tenga
el enlace, pero no se indexa en buscadores (`noindex` + `robots.txt`).

Secretos: `LALIGA_TOKENS` (contenido de tokens.json) y `GH_PAT` (token fine-grained de
este repo con permiso *Secrets: Read and write*). `config.json` sí va en el repo: no
contiene secretos.

## 4. Editorial con IA (opcional)

Con `ANTHROPIC_API_KEY` en el entorno, el editorial lo escribe un modelo a partir de los datos del
día (sin inventar cifras). Sin clave, usa plantillas.

## Personalizar

- **Afición** (`AFICION` en config.json): de qué equipo es cada mánager. La prensa rosa cruza
  los resultados reales de la jornada ("Luto en casa de X") y las plantillas ("culé de boquilla"
  si tiene jugadores del eterno rival). Vale "Madrid", "Barça", "Atleti", "Betis"…

- Titulares: diccionario `HEAD` en `lff/news.py` (mete los motes de tus amigos).
- Diseño: `lff/periodico.html`.
- Cada edición se archiva en `site/archivo/AAAA-MM-DD.html`.

Endpoints y flujo de login basados en el proyecto [Externoak/LaLigaApp](https://github.com/Externoak/LaLigaApp).
Proyecto no oficial, sin relación con LaLiga. Úsalo solo para tu liga y con calma: unas pocas
peticiones al día.
