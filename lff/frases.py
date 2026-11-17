"""Banco de frases del periódico. ¡Añade las tuyas!

Cada clave tiene una lista de variantes; el periódico elige una distinta cada día y no
repite la misma dentro de una edición. Lo que va entre llaves se rellena solo:
  {who}     el mánager que hace la operación      {other}   la otra parte
  {player}  el jugador                            {amount}  el dinero (ya formateado)
  {team}    un equipo de la liga                  {points}  puntos
  {club}    equipo real (Real Madrid, Barça…)     {n}, {days}, {pos}, {week}…
Si te inventas una frase, usa solo las llaves que ya aparecen en las otras de esa lista.
"""

FRASES = {
    # ───────────────────────── TITULARES DE MERCADO ─────────────────────────
    "clausulazo": [
        "¡CLAUSULAZO! {who} le arranca a {player} a {other} por {amount}",
        "Atraco a mano armada: {who} paga la cláusula de {player} ({amount})",
        "{other} no da crédito: {who} se lleva a {player} por la vía rápida",
        "¡ESCÁNDALO! {who} saquea a {other} y se lleva a {player} ({amount})",
        "Puñalada en el mercado: {player} abandona a {other} por {who}",
        "{who} entra sin llamar y sale con {player} bajo el brazo",
        "Golpe en la mesa: {who} ejecuta la cláusula de {player}",
        "{other}, desolado: {who} le roba a {player} a plena luz del día",
        "Sin piedad: {who} pone {amount} y se queda a {player}",
        "La cláusula de {player} salta por los aires: {who} lo ha hecho",
    ],
    "fichaje": [
        "{who} rompe la hucha: {player} llega por {amount}",
        "Bombazo en el mercado: {player} ficha por {who} ({amount})",
        "{who} se hace con {player} tras una puja de {amount}",
        "{player} ya tiene nuevo jefe: {who} paga {amount}",
        "Movimiento en los despachos: {who} cierra a {player} ({amount})",
        "{who} no se esconde y suelta {amount} por {player}",
        "¡BOMBA! {who} pone {amount} encima de la mesa y {player} dice sí",
        "{who} enloquece en el mercado: {amount} por {player}",
        "{player}, nuevo galáctico de {who}",
        "{who} gana la subasta: {player} es suyo por {amount}",
        "Fumata blanca: {player} jugará para {who}",
        "{who} saca la chequera: {amount} por {player}",
        "Operación relámpago: {who} se lleva a {player}",
    ],
    "compra": [
        "{who} negocia con {other} y se queda a {player} por {amount}",
        "Acuerdo cerrado: {player} cambia de manos de {other} a {who}",
        "Apretón de manos entre {who} y {other}: {player}, traspasado",
        "{other} cede y {player} se marcha a {who} por {amount}",
        "Negocio entre amigos (o no): {player} pasa de {other} a {who}",
        "{who} convence a {other}: {player} cambia de aires por {amount}",
    ],
    "venta": [
        "{who} hace caja: vende a {player} por {amount}",
        "Adiós, {player}: {who} lo vende y se embolsa {amount}",
        "{who} da la patada a {player}: fuera por {amount}",
        "Sin sentimientos: {who} vende a {player} por {amount}",
        "{player} hace las maletas: {who} ingresa {amount}",
        "{who} limpia el vestuario: {player}, vendido",
        "Lluvia de millones para {who}: {player} sale por {amount}",
        "{who} rompe con {player}. Él se va; los {amount} se quedan",
    ],
    "lider": [
        "{team} sigue mandando: líder con {points} puntos",
        "Nadie tose a {team}, que lidera con {points} puntos",
        "{team}, en lo más alto y sin vértigo",
        "El trono sigue siendo de {team}",
    ],
    "nuevo_lider": [
        "¡CAMBIO EN LO MÁS ALTO! {team} es el nuevo líder",
        "Golpe de estado: {team} asalta el liderato",
        "Hay nuevo rey en la liga: {team}",
        "{team} toma el poder",
    ],
    "subida": [
        "{team} se dispara: sube {n} {puestos} y ya es {pos}º",
        "{team} escala {n} {puestos}: ya es {pos}º",
        "Remontada en marcha: {team} trepa hasta el {pos}º",
        "{team} huele sangre y sube al {pos}º",
    ],
    "bajada": [
        "Crisis en {team}: cae {n} {puestos} hasta el {pos}º",
        "{team} se desinfla y baja al {pos}º puesto",
        "Alarma roja en {team}: ya es {pos}º",
        "{team}, en caída libre: {pos}º y bajando",
    ],
    "estrella": [
        "{player} arrasa: {points} puntos en la jornada {week}",
        "Exhibición de {player}: {points} puntos y la jornada a sus pies",
        "{player} se sale con {points} puntos",
        "{player}, de otro planeta: {points} puntos",
        "Show de {player}: {points} puntos",
        "{player} firma la jornada: {points} puntos",
    ],
    "estrella_dek_dueno": [
        "{owner} lo tiene en su equipo y se frota las manos.",
        "{owner} ya está mandando capturas al grupo.",
        "En casa de {owner} hay fiesta.",
        "{owner}, el más listo de la clase esta semana.",
    ],
    "estrella_dek_libre": [
        "Y nadie de la liga lo tiene en su plantilla.",
        "Libre en el mercado. ¿A qué esperáis?",
        "Sin dueño en la liga: alguien se lo está perdiendo.",
        "Nadie lo quiso. Ahora todos lo quieren.",
    ],
    "partido": [
        "{local} {ls}-{vs} {visitor}: el partido que movió la liga",
        "Lo que pasó en el {local}-{visitor} ({ls}-{vs})",
        "{local}-{visitor}: el {ls}-{vs} que nadie de la liga olvidará",
        "Crónica del {local} {ls}-{vs} {visitor}",
    ],
    "partido_goles": [
        "{local} y {visitor} firmaron un {ls}-{vs} de ida y vuelta.",
        "Festival en el {local}-{visitor}: {ls}-{vs} y espectáculo.",
        "Un {ls}-{vs} de los que se recuerdan entre {local} y {visitor}.",
    ],
    "partido_normal": [
        "{local} y {visitor} firmaron un {ls}-{vs}.",
        "El {local}-{visitor} terminó {ls}-{vs}.",
        "{ls}-{vs} entre {local} y {visitor}.",
    ],

    # ───────────────────────── REPORTAJES DE FICHAJES ─────────────────────────
    "art_clausulazo": [
        "{who} no ha pedido permiso: ha pagado {amount} por la cláusula de {player} ({desc}), y se lo ha arrebatado a {other}.",
        "Sin avisar y sin despedirse: {who} ha depositado {amount} y {player} ({desc}) deja de ser de {other}.",
        "La noticia ha caído como una bomba: {who} ha ejecutado la cláusula de {player} ({desc}). {other} se ha enterado por la app.",
    ],
    "art_venta": [
        "{who} ha decidido hacer caja con {player} ({desc}), y se embolsa {amount}.",
        "{who} ha puesto a {player} ({desc}) en el escaparate y ya no está: {amount} a la cuenta.",
        "Ni lágrimas ni despedidas: {who} vende a {player} ({desc}) por {amount}.",
    ],
    "art_compra": [
        "{who} y {other} han cerrado un acuerdo: {player} ({desc}) cambia de manos por {amount}.",
        "Tras una negociación que nadie vio venir, {player} ({desc}) pasa de {other} a {who} por {amount}.",
    ],
    "art_fichaje": [
        "{who} ha ganado la puja por {player} ({desc}) con una oferta de {amount}.",
        "{player} ({desc}) ya es de {who}, que ha pagado {amount} para llevárselo.",
        "{who} ha ido a por todas y se ha quedado con {player} ({desc}) por {amount}.",
    ],
    "art_caro": [
        "Ha pagado un {pct}% por encima de su valor de mercado ({value}): o sabe algo, o se ha dejado llevar.",
        "Un {pct}% más de lo que vale ({value}). En la liga ya hay quien habla de locura.",
        "Ha pagado un {pct}% de sobreprecio sobre sus {value}. El corazón manda más que la calculadora.",
    ],
    "art_barato": [
        "Y a buen precio: un {pct}% por debajo de su valor de mercado ({value}).",
        "Ganga del año: un {pct}% por debajo de sus {value}.",
        "Ojo al negocio: lo ha conseguido un {pct}% más barato de lo que vale ({value}).",
    ],
    "art_justo": [
        "Un precio en línea con su valor de mercado ({value}).",
        "Ni caro ni barato: lo que marca el mercado ({value}).",
        "Precio justo, sin regalos para nadie ({value}).",
    ],
    "art_venta_buena": [
        "Lo vende un {pct}% por encima de su valor ({value}): buen negocio.",
        "Saca un {pct}% más de lo que vale ({value}). Hay quien nace para vender.",
    ],
    "art_forma_buena": [": llega en plena forma.", ": está en un momento dulce.", ": viene enchufado."],
    "art_forma_mala": [". Toca esperar a que despierte.", ". Necesita reencontrarse.", ". De momento, ni frío ni calor."],
    "art_lider": [
        "{who} es líder con {points} puntos y no quiere que nadie se le acerque.",
        "{who} manda en la liga con {points} puntos y sigue apretando el acelerador.",
        "Desde el liderato ({points} puntos), {who} demuestra que no se conforma.",
    ],
    "art_persigue": [
        "{who} es {pos}º con {points} puntos, a {gap} del liderato de {leader}.",
        "Con {points} puntos y {gap} por detrás de {leader}, {who} ({pos}º) mueve ficha.",
        "{who} ({pos}º, {points} puntos) quiere recortar los {gap} que le separan de {leader}.",
    ],
    "art_victima": [
        " {other} pierde a una pieza importante y tendrá que reaccionar en el mercado.",
        " En casa de {other} ya buscan sustituto… y venganza.",
        " {other} queda tocado. Habrá respuesta.",
    ],
    "art_venta_extra": [
        " Habrá que ver en qué invierte el dinero.",
        " Ahora tiene la cartera llena y muchos ojos encima.",
        " El dinero ya quema en la cuenta.",
    ],
    "cierre_clausulazo": [
        "La respuesta de la víctima no se hará esperar.", "El vestuario ya comenta la jugada.",
        "Ahora le toca demostrar que valía la cláusula.", "Esto no ha hecho más que empezar.",
        "El grupo de WhatsApp arde.",
    ],
    "cierre_venta": [
        "Seguiremos informando.", "Ahora toca acertar con el siguiente fichaje.",
        "El tiempo dirá si fue un acierto.", "Más de uno ya le ha echado el ojo al dinero.",
    ],
    "cierre_fichaje": [
        "El vestuario ya comenta la jugada.", "Seguiremos informando.",
        "Ahora le toca demostrarlo en el campo.", "La afición ya hace cola para la camiseta.",
        "Se aceptan apuestas sobre su debut.", "El resto de la liga toma nota.",
    ],

    # ───────────────────────── PRENSA ROSA ─────────────────────────
    "g_culebron_t": ["Guerra fría entre {x} y {y}", "{x} y {y} ya no se saludan", "Tensión máxima entre {x} y {y}",
                     "La herida entre {x} y {y} sigue abierta"],
    "g_culebron": [
        "Desde que {who} le levantó a {player} a {other}, en el vestuario no se hablan. Fuentes de esta redacción aseguran que la cosa no ha terminado.",
        "Lo de {player} no se ha olvidado. Testigos aseguran que {other} ha silenciado a {who} en el grupo.",
        "{other} sigue sin perdonar a {who} por lo de {player}. Se habla de venganza en el próximo mercado.",
    ],
    "g_romance_t": ["{x} y {y}, inseparables", "{x} y {y}: amor de mercado", "Se buscan: {x} y {y}, siempre juntos"],
    "g_romance": [
        "Ya van {n} operaciones entre ellos. ¿Amistad, negocio… o algo más?",
        "{n} tratos en poco tiempo. El resto de la liga empieza a sospechar de un pacto secreto.",
        "Con {n} operaciones cruzadas, ya hay quien pide que la liga investigue.",
    ],
    "g_corazon_t": ["{who} se tira de los pelos: {player} hace {points}", "Lo que pudo ser y no fue: {player} brilla lejos de {who}",
                    "{who}, arrepentido: {player} se sale ({points})"],
    "g_corazon": [
        "Lo vendió por {amount} y en la jornada {week} se salió{donde}",
        "Lo dejó marchar por {amount}. En la jornada {week} le dio la razón a quien lo compró{donde}",
        "{amount} le dieron por él. La jornada {week} le ha costado mucho más{donde}",
    ],
    "g_sucesos_t": ["Escándalo: {who} se presenta con la alineación mal hecha", "Bochorno: {who} se olvida de alinear",
                    "{who}, pillado con la alineación en blanco"],
    "g_sucesos": [
        "Los servicios jurídicos de la liga estudian el caso. La afición, indignada.",
        "Fuentes cercanas apuntan a una siesta demasiado larga.",
        "El comité de competición ya ha abierto expediente. La grada exige explicaciones.",
    ],
    "g_drama_t": ["Luto en casa de {team}", "{team}, hundido", "Día negro para {team}"],
    "g_drama": [
        "Su {club} cayó {gf}-{gc} ante el {rival}. Nos cuentan que no ha querido hablar con nadie.",
        "El {gf}-{gc} de su {club} contra el {rival} le ha dejado sin ganas de abrir el grupo.",
        "Tras el {gf}-{gc} del {club} ante el {rival}, se le vio paseando cabizbajo.",
    ],
    "g_euforia_t": ["{team}, insoportable tras el {gf}-{gc} de su {club}", "{team} no cabe en sí: su {club} gana {gf}-{gc}",
                    "Fiesta en casa de {team}"],
    "g_euforia": [
        "Testigos aseguran que lleva desde el partido mandando audios al grupo.",
        "Ha cambiado la foto de perfil tres veces desde el pitido final.",
        "Fuentes de su entorno confirman que no ha dejado de hablar del partido.",
    ],
    "g_traicion_t": ["{team}, {apodo} de boquilla", "Traición en casa de {team}", "{team}: el corazón dice una cosa, la plantilla otra"],
    "g_traicion": [
        "Presume de {club}, pero en su plantilla tiene a {players}. La grada pide explicaciones.",
        "Dice ser del {club} de toda la vida, pero ahí están {players}. Sospechoso.",
        "¿Fiel al {club}? Su plantilla, con {players}, dice lo contrario.",
    ],
    "g_rumor_t": ["{player}, en la órbita de {target}", "{target} sueña con {player}", "Movimientos alrededor de {player}"],
    "g_rumor": [
        "Tras sus {points} en la jornada {week}, fuentes cercanas al mánager (que no han querido identificarse) aseguran que {target} ya prepara una puja.",
        "Se ha visto a {target} mirando la ficha de {player} varias veces al día. Nadie lo confirma; nadie lo desmiente.",
        "Según esta redacción, {target} habría preguntado por {player} tras sus {points}. Sin contrastar, pero con buena pinta.",
    ],
    "g_sebusca_t": ["¿Alguien ha visto a {team}?", "Se busca: {team}", "{team}, en paradero desconocido"],
    "g_sebusca": [
        "{dias} Su familia pide colaboración ciudadana.",
        "{dias} La última vez que se le vio, estaba mirando ofertas sin atreverse a pujar.",
        "{dias} Se teme que haya olvidado la contraseña.",
    ],
    "g_paron_t": ["Sin fútbol, {team} no suelta el móvil", "{team}, enganchado al mercado", "El parón saca lo peor de {team}"],
    "g_paron": [
        "{n} operaciones en una semana sin partidos. Su entorno empieza a preocuparse.",
        "{n} movimientos en siete días. Hay quien habla de adicción.",
        "Lleva {n} operaciones desde que paró la liga. Nadie sabe cuándo duerme.",
    ],
    "g_coleccion_t": ["{team} monta su propio {club}", "{team} y su obsesión por el {club}", "El {club} B se llama {team}"],
    "g_coleccion": [
        "Tiene a {n} jugadores del {club} en la plantilla: {players}. ¿Coincidencia?",
        "{players}… {n} jugadores del {club}. Ya hay quien le pide carnet de socio.",
    ],
    "g_hucha_t": ["{team}, el banco de la liga", "{team} vende y no compra", "Operación hucha en {team}"],
    "g_hucha": [
        "Ha ingresado {amount} en ventas esta semana sin fichar a nadie. ¿Para qué está ahorrando?",
        "{amount} en ventas y ni un fichaje. El resto de mánagers, mosqueados.",
    ],
    "g_todoa100_t": ["{team}, rey de las rebajas", "{team} compra al por mayor", "Mercadillo en casa de {team}"],
    "g_todoa100": [
        "{n} fichajes por menos de 3 M€ cada uno esta semana. La calidad, ya si eso, otro día.",
        "Ha fichado a {n} jugadores baratos en siete días. Cantidad antes que calidad.",
    ],
    "g_fantasma_t": ["Fichaje fantasma: {player} no aparece", "{who} paga {amount} por {player}… y {player} hace {points}",
                     "¿Dónde está {player}?"],
    "g_fantasma": [
        "{who} pagó {amount} y en la jornada {week} su fichaje sumó {points}. Las devoluciones no se aceptan.",
        "{amount} invertidos para {points} en la jornada {week}. {who} prefiere no hablar del tema.",
    ],

    # ───────────────────────── EDITORIAL ─────────────────────────
    "ed_lider": [
        "{leader} manda con {points} puntos y {gap} de ventaja sobre el segundo.",
        "{gap} puntos separan a {leader} ({points}) del resto. De momento, la liga tiene dueño.",
        "Arriba sigue {leader}, con {points} puntos y un colchón de {gap}.",
        "{leader} lidera con {points}. El segundo, a {gap}, sigue soñando.",
    ],
    "ed_gasto": [
        "En los despachos, {who} es quien más ha tirado de cartera ({amount}).",
        "El mercado tiene nombre propio: {who}, con {amount} gastados.",
        "{who} ha decidido que el dinero está para gastarlo: {amount} esta semana.",
    ],
    "ed_crack": [
        "En el césped, {player} ({points}) fue lo mejor para {owner}.",
        "{owner} sonríe gracias a {player} y sus {points}.",
        "{player} ({points}) le alegró la semana a {owner}.",
    ],
    "ed_farolillo": [
        "Mientras, {team} sigue buscando el camino desde el fondo.",
        "Abajo, {team} pide a gritos una reacción.",
        "{team}, último, ya no sabe a qué santo encomendarse.",
    ],
    "ed_cierre": [
        "La liga huele a pólvora.", "Se avecinan curvas.", "Aquí no se rinde nadie.",
        "Que nadie se relaje.", "Esto está más vivo que nunca.", "Palomitas.",
    ],

    # ───────────────────────── PARÓN ─────────────────────────
    "paron_t": [
        "Parón de selecciones: la liga contiene la respiración",
        "Sin fútbol, pero con mercado: la liga no descansa",
        "Semana en blanco: los mánagers, en modo despacho",
        "La liga duerme, los mánagers no",
    ],
    "paron_cuerpo": [
        "Es el momento de los despachos: quien se mueva ahora en el mercado llegará con ventaja a la vuelta.",
        "Sin partidos no hay excusas: es tiempo de planificar, fichar y, por qué no, soñar.",
        "Mientras los jugadores están con sus selecciones, los mánagers afilan los cuchillos.",
    ],
}

# ───────────────────────── ANUNCIOS (marcas inventadas) ─────────────────────────
# Llaves disponibles: {leader} {last} {team} {spender} {spent} {crack} {crack_owner} {paquete} {price}
ANUNCIOS = [
    {"brand": "EAU DE CLAUSULAZO", "style": "dark", "title": "La fragancia de los que no piden permiso",
     "text": "Notas de cartera abierta y madera de banquillo. Inspirada en {leader}.", "price": "{price}"},
    {"brand": "BUFANDAS EL SUPLENTE", "style": "box", "title": "Bufanda oficial de {team}",
     "text": "100% poliéster, 0% títulos. Abriga más que su delantera.", "price": "{price}"},
    {"brand": "SEGUROS FAROLILLO", "style": "classic", "title": "¿Último de la liga? Le cubrimos la vergüenza",
     "text": "Pregunte por nuestro Plan {last}: cobertura total contra memes del grupo.", "price": "Llame ya"},
    {"brand": "ACADEMIA EL ONCE BIEN PUESTO", "style": "box", "title": "Aprenda a alinear en 3 sencillas lecciones",
     "text": "Método probado. Primera clase gratis para quien salió con la alineación mal hecha.", "price": "Matrícula abierta"},
    {"brand": "EDICIONES DERROCHE", "style": "classic", "title": "Curso online: cómo fundirse {spent} en una semana",
     "text": "Impartido por {spender}. Incluye diploma y deudas.", "price": "{price}", "needs": "spender"},
    {"brand": "PELUCHES TITULAR", "style": "dark", "title": "Peluche oficial de {paquete}",
     "text": "Abrazable, lavable y, como el original, no alineable.", "price": "{price}", "needs": "paquete"},
    {"brand": "TEXTIL LA GRADA", "style": "box", "title": "Camiseta «Yo tengo a {crack}»",
     "text": "Edición limitada para la afición de {crack_owner}. Tallas de la S a la XXL de ego.",
     "price": "{price}", "needs": "crack"},
    {"brand": "GPS LOCALIZA-MÍSTER", "style": "classic", "title": "¿Su mánager no ficha? Lo encontramos",
     "text": "Rastreo 24h de mánagers desaparecidos. Discreción garantizada.", "price": "{price}"},
    {"brand": "TILA LA PRÓRROGA", "style": "box", "title": "Para los nervios del cierre de mercado",
     "text": "Recomendada por 9 de cada 10 mánagers que pujaron de más.", "price": "{price}"},
    {"brand": "COLCHONES EL BANQUILLO", "style": "dark", "title": "Descanse como sus suplentes",
     "text": "Tan cómodo que no querrá salir nunca. Como {last} de la parte baja.", "price": "{price}"},
    {"brand": "GAFAS VAR-ÓPTICA", "style": "classic", "title": "¿No vio venir aquel clausulazo?",
     "text": "Graduación especial para ver las ofertas antes que nadie.", "price": "2x1"},
    {"brand": "CERVEZAS LA JORNADA", "style": "dark", "title": "Para celebrar… o para olvidar",
     "text": "La única que acompaña igual una goleada que un 0-3 en casa.", "price": "{price}"},
    {"brand": "MUDANZAS EL TRASPASO", "style": "box", "title": "Movemos a su jugador en 24 horas",
     "text": "Especialistas en salidas por la puerta de atrás. Pregunte por nuestro servicio exprés.", "price": "Presupuesto sin compromiso"},
    {"brand": "PSICÓLOGOS EL DESCENSO", "style": "classic", "title": "¿Su equipo le quita el sueño?",
     "text": "Terapia de grupo los lunes. {last} ya tiene cita fija.", "price": "1ª sesión gratis"},
    {"brand": "TROFEOS EL PODIO", "style": "box", "title": "Grabamos su copa antes de ganarla",
     "text": "Ideal para optimistas. {leader} ya ha encargado tres.", "price": "{price}"},
    {"brand": "BANCO LA CLÁUSULA", "style": "dark", "title": "Préstamos rápidos para pujas desesperadas",
     "text": "Sin preguntas, sin avales, sin vergüenza. TAE: la que usted no quiera saber.", "price": "Solicítelo ya"},
    {"brand": "AGENCIA EL REPRESENTANTE", "style": "classic", "title": "¿Quiere vender caro? Hablamos nosotros",
     "text": "Comisión del 50%. Sus amigos no volverán a hablarle, pero cobrará bien.", "price": "Llame ya"},
    {"brand": "TALLER LA REMONTADA", "style": "box", "title": "Reparamos temporadas rotas",
     "text": "Último aviso para {last}: aún está a tiempo.", "price": "Diagnóstico gratis"},
    {"brand": "PIZZAS EL CARRUSEL", "style": "classic", "title": "Para ver la jornada sin levantarse",
     "text": "Pida la Familiar Clausulazo: lleva de todo y le sale caro.", "price": "{price}"},
    {"brand": "RELOJES EL MINUTO 93", "style": "dark", "title": "Para los que pujan en el último segundo",
     "text": "Precisión suiza. Puntualidad de mánager.", "price": "{price}"},
]
