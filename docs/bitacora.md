# Bitácora de desarrollo

Una entrada por sesión, la más reciente arriba. Formato: fecha, qué se hizo, qué se aprendió, problemas encontrados.











## 2026-11-26 — El token ya no queda en el registro de acceso

**Qué se hizo**
- Al dejar el servidor como servicio, el registro del sistema mostraba el token: uvicorn anota la ruta de cada pedido y la ruta lo lleva. Un filtro en `uvicorn.access` lo reemplaza por `<token>`.
- La prueba de punta a punta revisa ahora la salida estándar además de la de errores; antes solo miraba la segunda y no lo detectó.

**Qué se aprendió**
- Desactivar el logger no sirve: uvicorn reconfigura el registro al arrancar. Un filtro sí se conserva.

**Problemas encontrados**
- El token que alcanzó a quedar en el registro se cambió.

## 2026-11-26 — Servidor por HTTP para claude.ai y el celular (#21)

**Qué se hizo**
- `auditor mcp --http [--puerto 8765] [--dominio …]`: Streamable HTTP solo en `127.0.0.1`, en `/mcp/<token>`, con protección contra DNS rebinding y sin estado entre pedidos. Decisión [0014](decisiones/0014-servidor-por-http-con-tunel.md).
- Token de 256 bits creado una vez en la carpeta de datos con permisos 600 (o `AUDITOR_DIAN_TOKEN`). El comando dice dónde leerlo, sin imprimirlo.
- Prueba de punta a punta con el comando como subproceso: responde con el token; sin él o con otro, 404; con otro dominio, 421; con otro origen, 403.
- Guía en el README con Tailscale Funnel.

**Qué se aprendió**
- En claude.ai, el token en encabezados de un conector está en beta para pocas organizaciones; el conector sin inicio de sesión funciona en todos los planes. Por eso el secreto va en la ruta.
- Sin configuración, el SDK de MCP deja apagada la protección contra DNS rebinding.
- pytest-cov 7 ya no mide subprocesos: la prueba de punta a punta valida el comportamiento y otra, en proceso, cubre el código.

**Problemas encontrados**
- El SDK 2.3 ya no trae `httpx`; las pruebas usan `urllib`.

## 2026-11-27 — Reintentos de carga y registro en MCP

La lista de herramientas publica `idempotentHint` para las dos cargas de facturas y el registro de clientes. Las cargas reconocen los archivos y documentos ya ingresados, y registrar de nuevo el mismo NIT devuelve su historial. La prueba de `tools/list` comprueba las tres anotaciones y que la exportación a Excel queda fuera.

## 2026-11-26 — Nota crédito sobre varias facturas (#7)

**Qué se hizo**
- `duplicados_y_anulaciones` ya no descuenta el total completo de una nota de cada factura que cita. Si la nota suma lo mismo que todas sus facturas (±2,00), cada una descuenta su propio total; si no, sale como `anulada_sin_repartir` para que el contador la revise. Decisión [0013](decisiones/0013-nota-credito-sobre-varias-facturas.md).
- Tres pruebas nuevas: nota que anula dos facturas completas, nota que no cuadra con ninguna y nota que cita una factura sin cargar.

**Qué se aprendió**
- El XML de la nota no dice cuánto le toca a cada factura que cita; repartir en proporción sería inventar una cifra.

**Problemas encontrados**
- Ninguno.

## 2026-11-26 — Los seis informes se consultan desde el chat (#11)

**Qué se hizo**
- Tres herramientas MCP de lectura: `compras_por_proveedor`, `iva_compras_por_bimestre` y `no_validadas`. Reusan los informes SQL que ya existían y entregan resumen ya sumado, detalle con CUFE, nota y aviso, como `facturas_credito`. El servidor pasa de 11 a 14 herramientas.
- Pruebas con cifras calculadas a mano sobre los fixtures; manifiesto de la extensión, README, SPEC §10 y decisión 0007 actualizados.
- Issues y tablero público del proyecto en GitHub (Project "Auditor DIAN Core").

**Qué se aprendió**
- El README prometía "¿cuánto le compró a cada proveedor?", pero ninguna herramienta de lectura lo respondía: el agente habría tenido que sumar filas de `buscar_documentos`.
- Declarar como enum los parámetros `informe`, `tipo` y `medio_pago` rompería los plugins y dejaría códigos válidos sin búsqueda; se descartó (#12).

**Problemas encontrados**
- Ninguno.

## 2026-11-20 — README profesional y política de seguridad

**Qué se hizo**
- README rehecho para que quien llega al repositorio entienda en segundos qué es y por qué es seguro: insignias reales (pruebas, cobertura, versión, Python, licencia), GIF, una tabla de garantías de seguridad y cómo se cumple cada una, qué ve Claude, instalación, preguntas de ejemplo, las 11 herramientas con su efecto y un diagrama del flujo.
- `SECURITY.md`: cómo reportar una vulnerabilidad en privado, qué cuenta como vulnerabilidad y el modelo de seguridad, incluido lo que no cubre (las bases no van cifradas).
- La CI ahora prueba Python 3.11, 3.12 y 3.13 y exige el 100 % de cobertura, para que las insignias digan la verdad.

**Qué se aprendió**
- Cada afirmación del README se verificó contra el código. "Seis filtros" era cierto para `core` más `pro`, pero en este repositorio son cuatro.

## 2026-11-20 — Release 0.4.1 y el informe sin cronograma

**Qué se hizo**
- Release `v0.4.1` en GitHub con `auditor-dian-0.4.1.mcpb` y su SHA-256, e instrucciones de instalación para el contador. El README enlaza a la última versión para descargar el paquete. Antes de subirlo se revisó su contenido, incluido el paquete Python que lleva adentro: autor con el correo anónimo y sin datos reales.
- El informe ya no incluye la sección "Cronograma real frente al planeado", por decisión del equipo; también se quitó de la estructura del informe en los cronogramas de `core` y `pro`. El PDF queda en 4 páginas.

## 2026-11-20 — `core` es público

**Qué se hizo**
- Revisión previa a la publicación: historial completo, archivos, paquete `.mcpb` y caché del grafo. Se buscaron datos de facturas, claves, rutas personales, identificaciones y nombres reales.
- Se quitaron dos cédulas reales y el nombre de una persona de los archivos (código, prueba y bitácora); el paquete 0.4.1 se reconstruyó sin ellos.
- `core` se publicó en un repositorio nuevo con un único commit y el correo anónimo de GitHub; el historial completo queda privado en `auditor-dian-core-historial` (decisión [0012](decisiones/0012-publicacion-con-historial-aparte.md)).
- Comprobado sin iniciar sesión: el repositorio se clona, instala y pasa las 142 pruebas, y el GIF del README carga.

**Qué se aprendió**
- Los datos reales se cuelan por los ejemplos: una cédula real servía como caso límite en una prueba y en un comentario. Revisar contra las identificaciones y nombres de las bases reales, no solo buscar "datos", fue lo que los encontró.

## 2026-11-20 — v0.4.1

**Qué se hizo**
- Versión 0.4.1 con las dos aclaraciones del MCP que salieron al grabar el GIF: cómo cargar un ZIP con varios compradores y las autorretenciones del emisor.
- `dist/auditor-dian-0.4.1.mcpb` verificado como lo corre Claude Desktop: 23 de 23 comprobaciones con una carpeta de Descargas realista (facturas reales, ruido, ZIP dañados y copias), entre ellas que nada ajeno entre al cargar todo en un solo cliente.

## 2026-11-20 — GIF de demostración y dos ajustes que salieron de grabarlo

**Qué se hizo**
- `docs/img/demo-claude-code.gif` (46 s, 1 MB), enlazado en el README: Claude Code, conectado solo al servidor MCP, registra un cliente, carga sus facturas desde Descargas, deja fuera la exportación que es de otra persona y responde el IVA del bimestre 1 (40.500) con sus 3 CUFE. Grabado con `vhs` sobre una carpeta personal falsa con los fixtures sintéticos, un ZIP por factura como llegan por correo.
- Un ZIP con facturas de varios compradores ahora dice en `sin_asignar` cuáles son y que se puede cargar en cada cliente con `ingerir_facturas`, donde lo ajeno se rechaza solo.
- La descripción de `resumen_periodo` ya no sugiere "¿cuánto le retuvieron a este cliente?": las retenciones del XML son autorretenciones del emisor (FAT01) y ahora se le indica a Claude que no las presente como practicadas al cliente.
- El informe en LaTeX ya compila con la clase IEEE real (4 páginas): se extrajo `IEEEtran` del paquete oficial `texlive-publishers` de Ubuntu a `~/texmf`, sin permisos de administrador.

**Qué se aprendió**
- Los ensayos con Claude real encuentran fallas que las pruebas no ven. Con un ZIP mezclado, Claude le pidió al usuario que separara las facturas a mano, aunque cargarlas en el cliente era seguro. Y repitió como hecho que "al cliente le aplicaron retenciones", porque la propia descripción de la herramienta lo sugería.
- Con las herramientas de Claude Code habilitadas, Claude abre el ZIP con la terminal en vez de usar el MCP. Para mostrar lo que vería un contador en Desktop hay que dejarle solo las herramientas del MCP (`--tools ""`).
- Grabar fuera del repositorio evita que en pantalla aparezcan rutas con el nombre del usuario.

## 2026-11-20 — Informe final en LaTeX, formato IEEE

**Qué se hizo**
- El informe pasó de Markdown a LaTeX con la clase `IEEEtran` a doble columna: `docs/informe/informe.tex` y `referencias.bib` (biblatex, estilo `ieee`, con las fuentes de `docs/investigacion/`). Se borró `informe-final.md` para no mantener dos versiones.
- El resumen va como *abstract* con palabras clave, las fuentes como bibliografía numerada y se agregó una sección de conclusiones. El diagrama de arquitectura está en TikZ.
- Lo que espera datos reales sigue marcado en rojo con `\pendiente{}`.

**Problemas encontrados**
- `IEEEtran` no viene en la instalación de TeX del equipo (está en el paquete `texlive-publishers`). El documento se comprobó compilando una copia con `article` a dos columnas: sin errores ni citas sin resolver.

## 2026-11-20 — Borrador del informe final

**Qué se hizo**
- Primer borrador de `informe-final.md` con las 12 secciones del cronograma, armado solo con lo que ya estaba escrito en `docs/` de `core` y `pro`: investigación, decisiones, hitos y bitácora.
- Lo que todavía no existe queda marcado como **Pendiente** en vez de completarse con supuestos: señales de uso de los contadores de prueba, precios, explicación del adelanto frente al plan y fechas de publicación.

**Qué se aprendió**
- La regla "si no quedó escrito en `docs/`, no pasó" funcionó: el informe salió sin reconstruir nada de memoria. Las secciones flojas son justo las que dependen de usuarios reales.

## 2026-11-20 — v0.4.0: herramientas que se explican solas, NIT en cualquier formato y cada cliente aislado

**Qué se hizo**
- **Descripciones como las de un conector bien hecho** (por ejemplo el de Canva): cada herramienta tiene un título legible, que Claude Desktop muestra ("Cargar facturas y repartir por cliente"), una descripción con qué hace, cuándo usarla con frases reales del usuario y qué devuelve, y la descripción de cada parámetro. El texto llega corrido, sin los saltos de línea del código. Los parámetros comunes (cliente, fechas, año) están en `auditor_dian/parametros.py` y los usa también pro. Hay pruebas que exigen esto en todas las herramientas, y que el manifiesto de la extensión liste las mismas.
- **NIT o cédula en cualquier formato:** "NIT 900.000.009-0", "9000000090", "C.C. 79.123.456". El DV se quita si va tras un guion o si sobra por la cantidad de dígitos y es correcto según el algoritmo de la DIAN. Si queda en duda (una cédula corta con el DV pegado), se advierte al crear el cliente y al repartir. Una prueba genera 2.000 identificaciones al azar en 7 formatos.
- **Cada cliente aislado** ([decisión 0011](decisiones/0011-filtros-entre-clientes.md)), con seis filtros: al cargar facturas, al cargar documentos de renta (pro), al abrir la base, al consultar facturas, al consultar renta (pro) y al repartir. Una factura de la que el cliente no es comprador ni vendedor ya no se guarda. Las de consumidor final (`222222222222`) no se asignan a nadie.
- **Más casos límite:**
  - Ruta vacía o la carpeta personal completa: se rechazan.
  - PDF en vez de ZIP: se explica la diferencia.
  - Carpetas con mayúsculas distintas, tildes o "~": se encuentran.
  - Carpeta sin facturas: se avisa.
  - Exportar "en el Escritorio" sin nombre de archivo: se le pone uno automático.
  - Cliente sin documentos: su historial sale vacío.
  - Base copiada en la carpeta de otro cliente: se rechaza.

**Verificación**
- Con el `.mcpb` final, instalado como lo haría un contador: carpeta personal de prueba con las facturas reales en Descargas, más ruido realista (PDF, un ZIP de fotos, un ZIP dañado y una copia repetida con otro nombre en una carpeta con tildes), y ninguna ruta escrita. Pasan las 23 verificaciones:
  - 47 documentos repartidos entre sus clientes, y las facturas a consumidor final quedan sin asignar con su motivo.
  - Una cédula con el DV pegado se advierte y se corrige con una confirmación.
  - Cargar toda la carpeta de Descargas en un solo cliente: no entra nada ajeno.
- 142 pruebas en core y 232 en pro, ambas con cobertura del 100 %. La extensión de desarrollo expone 18 herramientas con nombres válidos para la API.

**Qué se aprendió**
- La verificación de punta a punta con datos reales encontró tres fallas que las pruebas unitarias no veían:
  - las facturas a consumidor final se ofrecían como un "cliente" por crear;
  - el NIT de una exportación (`EXT-000123`) se habría interpretado como el cliente `000123`;
  - la clave de los PDF bancarios fallaba cuando el NIT se escribía con puntos.
- Un hash no dice de quién es un documento: lo dice la identificación que trae adentro. Por eso los filtros usan esa identificación.

**Problemas encontrados**
- El conteo de documentos de la base de pruebas común bajó de 8 a 7: la exportación de ejemplo no es del cliente, y antes se guardaba.

## 2026-11-20 — v0.3.0: pensado para quien no sabe de rutas ni formatos

**Qué se hizo**
- Se asume un usuario sin conocimientos técnicos ([decisión 0010](decisiones/0010-carga-desde-claude.md), actualizada):
  - "Carga mis facturas" basta: sin ruta, `ingerir_por_cliente` revisa la carpeta de Descargas y reparte cada factura al cliente que la compró. Los compradores que no tienen cliente creado se devuelven con su nombre, para crearlos con un "sí".
  - Las carpetas se nombran como las ve el usuario ("facturas enero", "Escritorio/compras"): se buscan en la carpeta personal, Descargas, Escritorio y Documentos, en español o inglés.
  - El NIT se acepta con puntos, espacios o dígito de verificación (`900.000.009-9`), también en la CLI.
  - Las instrucciones del servidor le piden a Claude hablar en lenguaje sencillo, sin pedir rutas ni mostrar nombres de herramientas.
- Saber si un cliente ya está registrado: `listar_clientes` busca por parte del NIT o del nombre; la nueva `historial_cliente` muestra documentos por tipo y por mes de emisión y cada día de carga. `crear_cliente` sobre un cliente existente ya no falla: devuelve su historial sin cambiar nada, y al crear uno nuevo avisa si otro cliente tiene el mismo nombre (posible NIT mal escrito).
- Verificado con el `.mcpb` final como lo usaría un contador: carpeta personal de prueba con las 57 facturas reales sueltas en Descargas, carpeta de datos vacía y ninguna ruta escrita. Primer "carga mis facturas": 6 compradores sin cliente. Tras crearlos con el NIT escrito con puntos: 57 documentos en 6 clientes, sin errores; repetir no duplica. 125 pruebas en core (cobertura 100 %) y 228 en pro.

**Qué se aprendió**
- La interfaz para el usuario es Claude, pero el agente no conoce la carpeta personal del usuario: si el servidor exige rutas absolutas, Claude las inventa o le pide al usuario algo que no sabe dar. Resolverlo en el servidor es más confiable que instruir al modelo.

**Problemas encontrados**
- La primera versión devolvía el NIT tal como se escribió (con puntos y guion) y no el normalizado; lo detectó la prueba de instalación.
- Pendiente: en Windows con OneDrive, el Escritorio y Documentos suelen estar dentro de `OneDrive\`; no se buscan ahí todavía.

## 2026-11-20 — v0.2.0: listo para que un contador lo use desde Claude Desktop

**Qué se hizo**
- Carga desde Claude ([decisión 0010](decisiones/0010-carga-desde-claude.md)): herramientas `crear_cliente`, `ingerir_facturas` e `ingerir_por_cliente`, que reparte una carpeta con facturas de varios clientes según el comprador de cada archivo. Solo agregan: nada se borra ni se modifica.
- Herramienta `diagnostico` para reportar problemas sin montos: versión, carpeta de datos, plugins, conteos y advertencias de lectura por cliente.
- README con una guía para contadores (instalar, crear cliente, cargar, preguntar, reportar) y formularios de GitHub Issues: "Algo salió mal" y "Una cifra no cuadra".
- Manifiesto de la extensión actualizado (ya no dice "solo lectura") y versión 0.2.0.
- Verificado como lo instalaría un usuario nuevo: el `.mcpb` final desempacado en una carpeta limpia, corrido con `uv run` por stdio como lo hace Claude Desktop, con una carpeta de datos vacía. Las 57 facturas reales, mezcladas en una sola carpeta, quedaron repartidas en sus 6 clientes sin errores; recargar no duplicó nada; los casos límite (ruta relativa, NIT con DV, cliente repetido o inexistente, archivo que no es ZIP ni XML) dan mensajes claros. 115 pruebas, cobertura 100 %.

**Qué se aprendió**
- No hace falta un servidor en internet: el servidor MCP corre en el equipo de cada usuario y Claude Desktop lo lanza. Las facturas no salen del equipo salvo lo que Claude lee en la conversación.
- Sin carga desde Claude, la extensión era inútil para alguien que no usa la terminal: solo veía herramientas de consulta sobre ninguna base.

**Problemas encontrados**
- El repositorio es privado: los usuarios de prueba no pueden abrir Issues sin ser invitados. Por ahora reportan a quien les comparte la extensión, con el diagnóstico.

## 2026-11-20 — Limpieza de comentarios y docstrings

**Qué se hizo**
- Se quitaron docstrings y comentarios que repetían lo que ya dicen el código o los nombres (11 archivos, 30 líneas menos).
- Se conservaron las docstrings que cumplen una función: las de herramientas MCP (son la descripción que recibe el agente), las de comandos (son el `--help`) y las de la interfaz pública para plugins; y los comentarios que explican un porqué o citan una norma o el anexo técnico.

**Qué se aprendió**
- En las herramientas MCP y en typer la docstring no es documentación opcional: es parte del producto.

## 2026-11-20 — Herramientas descartadas por Claude Desktop: nombres no ASCII

**Qué se hizo**
- `App.herramienta` rechaza herramientas cuyo nombre o parámetros no acepta la API de Claude (decisión [0008](decisiones/0008-interfaz-de-plugins.md)); prueba de core que lo exige a las seis herramientas propias. En `pro`, `año` pasó a `anio` en la interfaz MCP.
- Verificación antes de entregar: paquete de desarrollo desempacado en carpeta limpia y probado por stdio, como lo corre Desktop; comprobación independiente de los nombres sobre el JSON que viaja; llamadas con datos reales y casos límite (nombre viejo, cliente inexistente, año inválido, año sin datos).

**Qué se aprendió**
- El cliente MCP de Python acepta cualquier nombre; la restricción está en la API de Claude y Desktop no avisa, solo omite la herramienta. Probar con el cliente MCP no basta: hay que validar contra la regla de la API.

**Problemas encontrados**
- Las herramientas de `pro` llegaron a Desktop sin poder usarse; lo detectó el usuario.

## 2026-11-20 — Plugins en la extensión de desarrollo

**Qué se hizo**
- `scripts/empaquetar_mcpb.sh --desarrollo RUTA...` agrega cada plugin en modo editable al paquete. Se probó desempacado en una carpeta limpia: expone las 6 herramientas de core más las del plugin, y responde sobre la base real.

**Qué se aprendió**
- `tool.uv.sources` solo vale en el proyecto raíz: la fuente local de core que declara el plugin no sirve dentro del paquete, por eso el paquete declara las fuentes de todos.

**Problemas encontrados**
- Ninguno.

## 2026-11-20 — Ficha de la extensión en Claude Desktop

**Qué se hizo**
- `long_description` del manifiesto reescrita en Markdown (qué se puede preguntar y cómo se cuidan los datos), para la vista de resumen de la extensión.

**Qué se aprendió**
- Las pestañas "Resumen" y "Permisos" que muestran conectores como Canva las dibuja Desktop. Una extensión local solo aporta los datos del manifiesto (descripción, ícono, herramientas) y las anotaciones de solo lectura de cada herramienta, que Desktop usa para agrupar los permisos.

**Problemas encontrados**
- No se puede forzar el diseño en pestañas desde la extensión; cambiar el manifiesto exige reinstalar el `.mcpb`, también en modo desarrollo.

## 2026-11-20 — Plugins: abrir la base para escribir

**Qué se hizo**
- `App.abrir` acepta `escritura=True` para los comandos de carga de un plugin. Se probó que por defecto sigue en solo lectura. Decisión [0008](decisiones/0008-interfaz-de-plugins.md) y SPEC §8 actualizados.

**Qué se aprendió**
- El SPEC de `pro` pedía una herramienta MCP `cargar_documento`; cargar por MCP rompería el principio de solo lectura del servidor, así que en `pro` cargar es un comando y consultar es la herramienta.

**Problemas encontrados**
- Ninguno.

## 2026-11-20 — Extensión de desarrollo

**Qué se hizo**
- `empaquetar_mcpb.sh --desarrollo` arma "Auditor DIAN (desarrollo)", que instala `core` en modo editable desde el repositorio. Se comprobó que el servidor que arranca carga `src/auditor_dian/servidor.py` del repositorio y responde 40.500.

**Qué se aprendió**
- Con la extensión normal hay que reempaquetar y reinstalar con cada cambio; con la de desarrollo basta con desactivarla y activarla en Desktop.

**Problemas encontrados**
- Ninguno.

## 2026-11-20 — Extensión de Claude Desktop (.mcpb)

**Qué se hizo**
- `scripts/empaquetar_mcpb.sh` arma `dist/auditor-dian-<versión>.mcpb`: manifiesto 0.4 con nombre "Auditor DIAN", descripción, logo, las seis herramientas y la carpeta de datos como configuración del usuario. Decisión [0007](decisiones/0007-servidor-mcp.md) actualizada.
- Prueba manual: el paquete descomprimido en una carpeta limpia arranca con `uv run` (40 paquetes instalados), se presenta como "Auditor DIAN 0.1.0" y responde 40.500 de IVA sobre la base de prueba.

**Qué se aprendió**
- Claude Desktop en Linux admite extensiones de tipo `uv`: ejecuta el `uv` que trae, en la carpeta de la extensión, con los argumentos del manifiesto.

**Problemas encontrados**
- Ninguno. Falta confirmar a ojo que Desktop muestra el logo después de instalar.

## 2026-11-20 — Claude Desktop con las facturas reales

**Qué se hizo**
- Claude Desktop apunta ahora a una base local con las 57 facturas reales: 6 clientes, uno por comprador, fuera de git. La configuración anterior, con la base de prueba, quedó respaldada.

**Qué se aprendió**
- La página de plugins de Claude Desktop no muestra el título, la descripción ni el ícono que declara el servidor; muestra el nombre de la configuración y un ícono genérico. Se comprobó que el servidor sí los envía. Para que Desktop los muestre habría que empaquetar el servidor como extensión de Desktop (`.mcpb`, con su manifiesto e ícono).

**Problemas encontrados**
- Ninguno.

## 2026-11-20 — El servidor MCP se presenta con nombre, resumen y logo

**Qué se hizo**
- El servidor MCP declara título, descripción, versión y el logo como ícono (PNG y SVG embebidos). El logo pasó de `docs/` a `src/auditor_dian/` para que viaje en el paquete instalado. Prueba nueva: el cliente MCP recibe los cuatro datos. Decisión [0007](decisiones/0007-servidor-mcp.md) actualizada.

**Qué se aprendió**
- MCP permite íconos en la información del servidor, pero mostrarlos es decisión de cada cliente; se verifica a ojo en Claude Desktop tras reiniciarlo.

**Problemas encontrados**
- Ninguno.

## 2026-11-20 — Medios de pago

**Qué se hizo**
- El parser guarda los medios de pago (`PaymentMeansCode`, tabla 13.3.4.2 de la Caja de Herramientas FE 1.9) como lista, y la columna que guardaba la forma de pago se llama ahora `forma_pago`. Esquema versión 3 ([decisión 0005](decisiones/0005-esquema-de-la-base.md)).
- La herramienta MCP `buscar_documentos` filtra por medio de pago y muestra forma y medios en cada fila.
- Se reconstruyó la base demo sintética de Claude Desktop con el esquema nuevo; sigue respondiendo 40.500 de IVA en el bimestre 1.

**Qué se aprendió**
- En las 57 facturas reales: 10 con tarjeta débito (`49`), 15 con tarjeta crédito (`48`, 9 de ellas junto a `ZZZ`), 11 en efectivo (`10`, 1 junto a `ZZZ`), 6 con `91` (nota bancaria transferible, un código raro para ventas al detal), 4 con transferencia débito interbancaria (`46`), 3 con consignación (`42`), 5 solo con `ZZZ` (otro) y 3 con `1` (instrumento no definido).
- Decidir cuáles de esos códigos cuentan como "medio electrónico" para la deducción del 1 % es una regla tributaria: queda para las reglas versionadas de `pro`, no para `core`.
- Un ejemplo oficial de la DIAN usa el código `54`, que no está en la tabla 13.3.4.2.

**Problemas encontrados**
- La base demo quedó en la versión 2 y el servidor la habría rechazado; se reconstruyó.

## 2026-11-20 — Fase 0: investigación de la necesidad

**Qué se hizo**
- Tres notas con fuentes públicas en `docs/investigacion/`: [cifras](investigacion/cifras-dian.md), [normas vigentes](investigacion/normas-vigentes.md) y [herramientas existentes](investigacion/herramientas-existentes.md). Cada cifra lleva su fecha de corte; las que vienen de prensa o de contenido patrocinado se marcan así.

**Qué se aprendió**
- En 2023 se emitieron 2.326,8 millones de facturas electrónicas; hay unos 1,16 millones de facturadores y 334.685 contadores activos.
- Solo el 19,7 % de las facturas a personas naturales sirve para la deducción del 1 % en renta, porque el resto no informa pago electrónico. Es una idea de informe para `pro`, y exige guardar el medio de pago, que hoy el parser no lee.
- La DIAN eliminó los portales de descarga: el ZIP con `AttachedDocument` que llega al correo de recepción es el insumo universal del comprador, que es lo que lee `core`.
- La Resolución 227 de 2025 compila (no reemplaza) la 165 y la 167; la 202 de 2025 no cambia el Anexo Técnico.
- Alegra ya tiene un MCP de solo lectura sobre su contabilidad: es la competencia más cercana. La diferencia es partir del XML recibido, sin depender del software contable, y en local.

**Problemas encontrados**
- El micrositio de cifras de la DIAN no publica totales de documentos validados por año; la cifra más reciente verificada es la de 2023. La de 2024 (más de 3.103 millones) es de prensa.
- No se leyó completo el Título 5 de la Resolución 227 de 2025 (la página es muy grande); queda pendiente confirmar las versiones de los anexos que cita.

## 2026-11-20 — Prueba con los XML de ejemplo oficiales de la DIAN

**Qué se hizo**
- En el correo del equipo no hay notas débito, documentos soporte, facturas en otra moneda ni con retenciones del emisor. En lugar de buscar facturas de terceros en internet (serían datos reales de otras personas), se usaron los 37 XML de ejemplo que la DIAN publica en la carpeta "Ejemplificaciones" de la Caja de Herramientas FE 1.9.
- El parser leyó los 37 sin errores ni advertencias. Cubren tipos `01`, `02`, `03`, `91` y `92` (notas con y sin factura de referencia), documentos en USD, retenciones `05` y `06`, y tributos nuevos (`22`–`24`, `32`–`36`, `ZZ`).
- Los ejemplos quedan en `data/dian-ejemplos/`, fuera de git: traen NIT y cédulas que podrían ser de personas reales.

**Qué se aprendió**
- La dirección de la TRM ya no es ambigua: `SourceCurrencyCode` es la moneda del documento (hallazgo 2 de [investigacion/anexo-tecnico.md](investigacion/anexo-tecnico.md)).
- Los ejemplos de 2019 restan el anticipo del total a pagar; la regla vigente (FAU14, numeral 11.9.2) ya no lo hace (hallazgo 4).

**Problemas encontrados**
- No hay ejemplos públicos de documento soporte (05/95) ni de factura tipo `04`; siguen cubiertos solo por fixtures sintéticos.

## 2026-11-20 — Licencia, nombre y logo

**Qué se hizo**
- Licencia MIT (`LICENSE`, `pyproject.toml`) y nombre público **Auditor DIAN**, sin renombrar el paquete ni el comando. El README aclara que no es un producto oficial de la DIAN. Logo propio en `docs/logo.svg`. Decisión [0009](decisiones/0009-licencia-y-nombre.md); SPEC §14 actualizado.
- Se buscaron en el correo del equipo facturas de tipos que faltan (nota débito, documento soporte, retenciones, moneda extranjera): no hay. Hay que pedirlas a un contador o una empresa.

**Qué se aprendió**
- Un logo que use la sigla DIAN no debe imitar los símbolos ni los colores de la entidad, para que nadie lo tome por oficial.

**Problemas encontrados**
- Ninguno.

## 2026-11-20 — Cotejo de las tablas de códigos con la Caja de Herramientas FE 1.9

**Qué se hizo**
- Se descargó de dian.gov.co la Caja de Herramientas de factura electrónica 1.9 y se cotejaron sus tablas contra lo que usa el código: tipos de documento (13.1.3), tipos de identificación (13.2.1), tributos (13.2.2) y formas de pago (13.3.4.1). Resultado en [investigacion/anexo-tecnico.md](investigacion/anexo-tecnico.md).
- Todo coincide salvo una cosa: existe el tipo `04` ("Factura electrónica de Venta - tipo 04"), que el informe de anulaciones no contaba como factura. Se agregó; la prueba de anulaciones usa ahora una factura tipo 04.
- El informe de retenciones muestra el nombre del tributo (ReteIVA, ReteRenta, ReteICA) junto al código.

**Qué se aprendió**
- El ZIP trae dos juegos de tablas: las listas `.gc` de "Listas de valores" son de una versión anterior (con "ReteFuente" y "ReteCREE"); las `.xlsx` de "Tablas Referenciadas" son las de la 1.9.
- El código `03` no es "contingencia DIAN" sino el instrumento electrónico que transcribe una factura de talonario o papel.

**Problemas encontrados**
- El del tipo `04`, corregido.

## 2026-11-20 — Plugin instalado como paquete real

**Qué se hizo**
- Se empaquetó `tests/plugin_ejemplo.py` como paquete aparte (`plugin-ejemplo`, con su entry point) y se instaló con `uv pip` en un entorno nuevo junto a `core`. Funcionaron sus tres aportes: el lector ingirió un tiquete, `auditor informe ... compras_por_tipo` lo mostró y `auditor mcp` expuso 7 herramientas, la del plugin incluida.

**Qué se aprendió**
- Si la herramienta de un plugin no encontraba al cliente, el agente recibía solo "Error executing tool": `app.abrir` lanzaba un error que el SDK de MCP oculta. Ahora usa la misma apertura que las herramientas de core (`servidor.abrir_cliente`), que convierte el error en `ToolError` con su motivo. Hay prueba.
- Un cliente MCP por stdio no hereda las variables de entorno si no se le pasan: `AUDITOR_DIAN_HOME` debe ir en la configuración del servidor, como en el README.

**Problemas encontrados**
- El de arriba, corregido.

## 2026-11-20 — Prueba en Claude Desktop

**Qué se hizo**
- Claude Desktop (Linux), con el servidor `auditor-dian` sobre la base de demostración, respondió "¿Cuánto IVA facturado en compras hubo en el bimestre 1 de 2026 para el cliente 900000009?" con 40.500, la misma cifra de Claude Code y de la prueba escrita a mano. Queda cumplido lo que pedía M4: probado en Claude Desktop y Claude Code.

**Qué se aprendió**
- Desktop lee `claude_desktop_config.json` solo al arrancar: hay que salir de la app por completo (no basta cerrar la ventana) y abrirla de nuevo.
- Antes del reinicio, Desktop no inventó la cifra: dijo que no tenía datos y pidió los archivos.

**Problemas encontrados**
- Ninguno.

## 2026-11-20 — M5: interfaz de plugins y `core` v0.1

**Qué se hizo**
- `src/auditor_dian/plugins.py`: `core` carga los plugins del grupo de entry points `auditor_dian.plugins` al empezar cualquier comando y le entrega a cada uno un `App` con cuatro métodos (`herramienta`, `informe`, `lector`, `abrir`).
- Plugin de ejemplo en `tests/plugin_ejemplo.py`, que usa los cuatro. Pruebas: core sin plugins, plugin que agrega informe, lector y herramienta MCP, plugin roto que se salta, lector que falla, y que un plugin no puede reemplazar nada de core.
- Se configuró Claude Desktop con el servidor `auditor-dian` sobre una base de demostración sintética (`data/demo/`, fuera de git); la configuración anterior quedó respaldada.
- 98 pruebas, cobertura 100 %. Decisión [0008](decisiones/0008-interfaz-de-plugins.md). M5 cerrado ([hitos/M5.md](hitos/M5.md)) y etiqueta `v0.1.0`.

**Qué se aprendió**
- El SDK de MCP, ante dos herramientas con el mismo nombre, conserva la primera y solo avisa en el log: hay que revisar antes de registrar.
- `anyio.run` no funciona dentro de un bucle asíncrono ya corriendo; los plugins se cargan antes de arrancar el servidor.

**Problemas encontrados**
- Un fixture de M2 (`factura_cargo_01.xml`) repetía el CUFE de la factura de exportación, que por eso nunca se guardaba en la base común de pruebas. Una prueba de los informes pasaba sin probar nada. Se corrigió.

## 2026-11-20 — M4: servidor MCP

**Qué se hizo**
- `auditor mcp` inicia un servidor MCP por stdio con las seis herramientas del SPEC (`src/auditor_dian/servidor.py`). Cada llamada abre la base en solo lectura, los montos salen como texto exacto y cada respuesta lleva el aviso del SPEC.
- `resumen_periodo` corre un SQL nuevo (`informes/resumen_periodo.sql`) que entrega cada cifra ya sumada, con sus CUFE.
- `exportar_informe` solo crea `.xlsx` nuevos, en rutas absolutas.
- 92 pruebas, cobertura 100 %: cada herramienta con el cliente MCP en memoria y una de punta a punta por stdio.
- Prueba con un agente real: Claude Code en modo no interactivo respondió la pregunta del criterio de aceptación con la cifra (40.500) y los CUFE correctos.
- Instrucciones para conectar Claude Code y Claude Desktop en el README. Decisión [0007](decisiones/0007-servidor-mcp.md). M4 cerrado ([hitos/M4.md](hitos/M4.md)).

**Qué se aprendió**
- El SDK `mcp` ya va en la versión 2: `FastMCP` se llama ahora `MCPServer` y la mayoría de los ejemplos públicos están desactualizados.
- Un error cualquiera dentro de una herramienta le llega al agente solo como "Error executing tool"; para que vea el motivo hay que lanzar `ToolError`.
- El agente citó la cifra sin recalcularla y repitió el aviso, porque `resumen_periodo` ya la entrega sumada.

**Problemas encontrados**
- Ninguno en el código. Falta probarlo en Claude Desktop, que no está en esta máquina.

## 2026-11-20 — Cierre de M3: cotejo automático contra los PDF

**Qué se hizo**
- El equipo preguntó si la revisión manual de 10 documentos era necesaria. Se reemplazó por `scripts/cotejar_pdf.py`, que busca el total de cada XML en el PDF del mismo ZIP, y se cambió el criterio en SPEC §13.
- Resultado con los 57 documentos reales: 53 coinciden exacto, 3 difieren solo porque el PDF redondea (a la decena o sin centavos) y 1 PDF es una imagen sin texto.
- M3 queda cerrado ([hitos/M3.md](hitos/M3.md)).

**Qué se aprendió**
- El PDF no siempre muestra lo mismo que el XML: hay emisores que lo redondean. El documento legal es el XML, y los informes toman siempre su valor.
- Un emisor escribe los montos en formato inglés y con 3 decimales (`427,468.066`), así que el cotejo lee cada cifra en los dos formatos.
- Cotejar 57 documentos de forma automática da más evidencia que revisar 10 a mano, y se puede repetir con cada lote nuevo.

**Problemas encontrados**
- El script necesita `pdftotext` (poppler), instalado en el sistema. No es dependencia de `core`.

## 2026-11-20 — Cambio de alcance: `facturas_credito` solo por forma de pago

**Qué se hizo**
- El equipo decidió que una factura es a crédito solo si su forma de pago es `2` (Crédito). Se actualizó SPEC §7: la fecha de vencimiento se sigue mostrando, pero ya no decide.
- Nueva prueba: una venta de contado con vencimiento a 30 días no aparece en el informe. 80 pruebas, cobertura 100 %.

**Qué se aprendió**
- Con las facturas reales, el informe pasó de 17 documentos a 5. Las 12 compras de contado que salían como crédito (droguería y transporte) ya no aparecen.

**Problemas encontrados**
- Ninguno.

## 2026-11-20 — M3 paso 5: material para la revisión manual

**Qué se hizo**
- Se generó `compras_por_proveedor` en Excel para las tres bases con facturas reales (`data/revision/`, fuera del repo) y se extrajeron los 57 PDF que venían en los ZIP, para cotejar contra ellos.
- Se escribió [hitos/M3.md](hitos/M3.md). M3 queda abierto hasta que una persona coteje al menos 10 documentos, como pide el SPEC.

**Qué se aprendió**
- Todas las facturas reales traen el PDF dentro del ZIP: se puede revisar sin pedir nada al emisor.

**Problemas encontrados**
- Ninguno.

## 2026-11-20 — M3 paso 4: exportación a Excel

**Qué se hizo**
- `auditor informe ... --xlsx salida.xlsx` guarda el informe con dos hojas: `resumen` (título, rango, nota del informe y tabla) y `detalle` (una fila por documento, con su CUFE).
- Los montos van exactos, con formato `#,##0.00`: Excel muestra 2 decimales pero suma con el valor completo (decisión 0006). Hay una prueba con un total de 6 decimales.
- Se agregó `openpyxl` 3.1.5, que ya figuraba en el stack del SPEC. 79 pruebas, cobertura 100 %.

**Qué se aprendió**
- En openpyxl, `hoja.cell(fila, columna)` crea la celda aunque solo se quiera consultarla: usarla para fijar el encabezado dejaba una fila vacía entre el encabezado y los datos. La prueba lo detectó.

**Problemas encontrados**
- Ninguno más.

## 2026-11-20 — M3 paso 3: duplicados, facturas a crédito y no validadas

**Qué se hizo**
- `duplicados_y_anulaciones`: mismo emisor y número con distinto CUFE, y facturas citadas por notas crédito (por CUFE, o por número si la nota no trae CUFE). La anulación es total si las notas suman el total de la factura con ±2,00; si no, parcial. Las notas cuentan aunque sean de otra fecha que la factura.
- `facturas_credito`: vencimiento posterior a la emisión o forma de pago `2` (Crédito, Anexo DS 1.1 tabla 16.3.4.1). Columna `eventos` = "por verificar".
- `no_validadas`: sin respuesta DIAN (`sin_respuesta`) o rechazadas (`rechazada`), con el archivo de origen.
- Ya están los seis informes del SPEC. 76 pruebas, cobertura 100 %.

**Qué se aprendió**
- Con las facturas reales: una factura de telecomunicaciones aparece anulada en parte por su nota crédito, y la factura que llegó como XML suelto, sin contenedor, sale como `sin_respuesta`.
- **Falso positivo en `facturas_credito`**: un emisor de droguería pone fecha de vencimiento a 60 días en ventas de contado (forma de pago `1`); dos empresas de transporte, a 1 día. Con la regla del SPEC ("vencimiento posterior **o** crédito") 12 compras de contado salen como crédito. Se dejó la regla del SPEC y el informe muestra `forma_pago` y `dias_plazo`; queda para decidir si basta la forma de pago.
- La consulta de un informe no puede abrir su propio `WITH`, porque ya corre dentro del que define `docs`: se escriben subconsultas.

**Problemas encontrados**
- Una nota crédito que cite varias facturas descuenta su total completo de cada una. No hay caso real; quedó anotado en el SQL.

## 2026-11-20 — M3 paso 2: `iva_compras_por_bimestre` y `retenciones`

**Qué se hizo**
- `iva_compras_por_bimestre`: IVA (tributo `01`) por bimestre fijo y tarifa, neto de notas crédito. La nota del informe aclara que no es una determinación de IVA descontable.
- `retenciones`: retenciones por mes y código de tributo. La nota aclara que en facturas y documento soporte son autorretenciones declaradas por el emisor.
- 73 pruebas, cobertura 100 %. Nuevo caso de prueba: una factura que repite el IVA 19 % en dos subtotales queda en una sola fila por tarifa.

**Qué se aprendió**
- Con las facturas reales el IVA sale en 5, 19 y 0 % y en varios bimestres. Ninguna trae retenciones, así que ese informe solo está probado con fixtures.

**Problemas encontrados**
- Los códigos de retención se muestran sin nombre: la tabla de códigos sigue sin cotejar contra la Caja de Herramientas DIAN.

## 2026-11-20 — M3 paso 1: primer informe, `compras_por_proveedor`

**Qué se hizo**
- Se aprobaron las siete reglas comunes de los informes (decisión [0006](decisiones/0006-reglas-de-los-informes.md)): redondeo solo al presentar, sin conversión de moneda, signos por tipo de documento, anulación total o parcial con tolerancia ±2,00, `no_validadas` con rechazadas, IVA solo con el tributo `01`, bimestres y meses fijos.
- Nueva carpeta `src/auditor_dian/informes/`: cada informe es un `.sql` de detalle y otro de resumen. Primer informe: `compras_por_proveedor`, con totales por NIT emisor y moneda.
- Nuevo comando `auditor informe <id> <informe> --desde --hasta`. Abre la base en solo lectura e imprime el resumen a 2 decimales en formato colombiano.
- 70 pruebas (eran 61), cobertura 100 %. Los valores esperados se escribieron a mano a partir de los fixtures.

**Qué se aprendió**
- Hacía falta filtrar por adquirente: sin ese filtro, el lote reenviado con facturas de cinco personas contaba 45 compras en vez de 26. Los informes solo cuentan los documentos a nombre del cliente.
- El nombre de un emisor varía entre documentos ("ÉXITO" / "EXITO"); por eso el resumen agrupa solo por NIT.

**Problemas encontrados**
- Ninguno. Falta `--xlsx`, que llega en el paso 4.

## 2026-11-20 — 45 facturas reales más: se levanta la salvedad de M1

**Qué se hizo**
- Una conocida de un integrante reenvió 45 facturas `01` de 2025–2026 (supermercados, droguerías, domicilios, aerolínea, transporte terrestre, cine, ropa, seguros). Se guardaron en una carpeta propia dentro de `data/` (ignorada por git) y se ingirieron en una base temporal.
- Resultado: 45 de 45 leídas sin errores ni advertencias del parser, todas validadas por la DIAN y cuadradas contra la regla FAU14. Reingesta sin duplicados; ningún CUFE se repite entre los tres lotes.
- Total de documentos reales: **57, de 20 emisores**. Se cumplen las condiciones de la salvedad de M1 y se levanta ([M1.md](hitos/M1.md)); se actualizaron M2.md y el cronograma.

**Qué se aprendió**
- El lote traía facturas de 5 adquirentes distintos. Al ingerirlo como un solo cliente, la advertencia `adquirente_distinto` marcó exactamente las 19 ajenas: primera prueba real de esa regla.
- Aparece el impuesto `22` (bolsas plásticas), que se liquida por unidad (`PerUnitAmount` × `BaseUnitMeasure`, FAS09–FAS11): su `base` es una cantidad. El valor es correcto; queda como regla para los informes de M3.
- El criterio de aceptación de v0.1 (50 documentos reales sin errores no explicados) ya se cumple en volumen. Falta variedad de tipos: todo es `01` salvo una nota crédito.

**Problemas encontrados**
- Ninguno en el código. Los documentos incluyen datos de terceros (otros adquirentes): se quedan en la máquina local y nunca entran al repo.

## 2026-11-20 — Totales completos del documento (esquema versión 2)

**Qué se hizo**
- El parser lee ahora todo el grupo `LegalMonetaryTotal`: `TaxInclusiveAmount`, `AllowanceTotalAmount`, `ChargeTotalAmount`, `PrepaidAmount` y `PayableRoundingAmount` (Anexo FE 1.9: FAU06, FAU08, FAU10, FAU12, numeral 5.2.1). Se guardan en cinco columnas nuevas de `documentos`; el esquema pasa a la versión 2 (actualización de la decisión 0005).
- Fixture sintético `factura_cargo_01.xml`, que reproduce sin datos reales el caso de la factura con cargo global. Prueba de ida y vuelta con redondeo negativo. 61 pruebas, 100 % de líneas.
- Llegó un documento real más (factura de telefonía de noviembre de 2026, con IVA e INC): 12 en total, todos sin advertencias.
- Se actualizó graphify a la versión 0.9.113, la misma de la skill.

**Qué se aprendió**
- El anexo valida `PayableAmount = TaxInclusiveAmount − AllowanceTotalAmount + ChargeTotalAmount` (FAU14) con tolerancia de ±2,00 (5.2.1.1). Los 12 documentos reales la cumplen exacto.
- El valor que anuncia el correo del emisor puede no coincidir con el XML (40.122,06 frente a 40.122,30): la fuente es siempre el XML.
- La tabla del anexo escribe "PrePaidAmount", pero el XPath del mismo anexo y UBL 2.1 usan `PrepaidAmount`, que es lo que traen los XML reales.

**Problemas encontrados**
- Ninguno. La base versión 1 de prueba se rechazó con el mensaje esperado y se volvió a crear.

## 2026-11-20 — Facturas reales de un familiar (después del cierre de M2)

**Qué se hizo**
- Un familiar de un integrante reenvió 9 documentos por correo (con su consentimiento): 8 facturas `01` y 1 nota crédito `91`, de 7 emisores, emitidos entre 2020 y 2025. Se guardaron en `data/papa/` (ignorada por git) y se ingirieron como un cliente aparte en una base temporal.
- Resultado: 9 de 9 leídos sin advertencias, 8 validados por la DIAN; reingesta sin duplicados. La nota crédito referencia una factura que también está en la base (el cruce de M3 funcionará).
- Total de documentos reales probados: 11.

**Qué se aprendió**
- Un ZIP trae la factura sola (`fv…xml`, sin `AttachedDocument`): se lee bien y `validado_dian` queda desconocido, como debe.
- Hay emisores que declaran un `TaxSubtotal` por línea con la misma tarifa (hasta 7 de IVA 19 %); los informes deben agrupar por código y tarifa.
- Aparece el impuesto `04` (INC) con base parcial, y documentos de 2020 (Anexo anterior a la 1.9) que se leen sin cambios.
- El total declarado puede diferir 1 centavo de subtotal + impuestos por el redondeo del emisor; M3 necesita una tolerancia explícita.

**Problemas encontrados**
- Una factura trae un cargo (`ChargeTotalAmount` = 55.460) que el parser no lee, así que su total no cuadra con subtotal + impuestos. Queda como pendiente de M3 en [M2.md](hitos/M2.md); es el primer caso real que obliga a cambiar el parser y debe volverse fixture anonimizado.

## 2026-11-20 — Cierre de M2

**Qué se hizo**
- Se cerró M2 ([resumen](hitos/M2.md)): esquema DuckDB versión 1, ingesta idempotente y comandos `clientes crear` e `ingerir`. 59 pruebas, 100 % de líneas.
- Decisión [0005](decisiones/0005-esquema-de-la-base.md): una base por cliente, tablas hijas para listas, idempotencia por SHA-256 y CUFE, `id_cliente` solo dígitos.
- Se marcó el cronograma y se regeneró el grafo de conocimiento completo (código y documentos).
- Primeras facturas reales: el correo de un integrante tenía solo 2 con ZIP adjunto (Cancillería y una universidad, tipo `01`). Se guardaron en `data/correo/` (ignorada por git). Parser e ingesta: 0 advertencias, ambas validadas por la DIAN, reingesta sin duplicados. No obligaron a cambiar el código, así que no generan fixture.

**Qué se aprendió**
- El criterio de cierre de M2 se puede probar con fixtures sintéticos, pero la salvedad de M1 no: sin facturas reales no se cumple el criterio de aceptación de v0.1.
- Los XML reales traen montos con 4 decimales (`116600.0000`), lo que confirma la decisión 0004. Una trae IVA con tarifa 0 % y base completa; la otra, una línea sin impuestos. Unidades `EA` y `94`.
- Un correo personal da pocas facturas: hay que pedir factura electrónica en cada compra y conseguir ZIPs de conocidos para llegar a 30–50.

**Problemas encontrados**
- La salvedad de M1 (facturas reales) no se cumplió antes de terminar M2, como se había pedido. Pasa a M3 como condición de cierre, sin más aplazamientos.

## 2026-11-20 — M2, paso 3: comandos `clientes crear` e `ingerir`

**Qué se hizo**
- `auditor clientes crear <id> --nombre "..."` y `auditor ingerir <id> <ruta>` (SPEC §9). `ingerir` imprime un resumen (archivos nuevos y ya ingeridos, documentos guardados, CUFE ya existentes, advertencias, errores de lectura) y remite a la tabla `advertencias` para el detalle.
- Códigos de salida: 0 si todo quedó registrado (aunque haya advertencias o errores de lectura, que quedan guardados); 1 si un archivo no se pudo guardar o el cliente no existe; 2 si la ruta no existe.
- Prueba de humo con el comando instalado sobre `tests/fixtures/`: 6 documentos la primera vez, 0 la segunda. 59 pruebas, 100 % de líneas.

**Qué se aprendió**
- Nada nuevo; los errores de uso (identificación con DV, cliente inexistente) se explican en el mensaje con el comando a usar.

**Problemas encontrados**
- Ninguno.

## 2026-11-20 — M2, paso 2: ingesta idempotente

**Qué se hizo**
- `ingesta.py`: `ingerir(con, id_cliente, ruta)` guarda las lecturas del parser en la base del cliente y devuelve un resumen (archivos nuevos y repetidos, documentos, CUFE repetidos, advertencias, errores, archivos que no se pudieron guardar).
- Idempotencia: un archivo con SHA-256 ya registrado se salta completo; un CUFE ya guardado no se inserta de nuevo y queda la advertencia `cufe_repetido`. Prueba del criterio de cierre: reingerir la misma carpeta deja todas las tablas iguales.
- Advertencias nuevas: `adquirente_distinto` (el documento se guarda igual, SPEC §6), `documento_sin_cufe` (no se guarda), `error_lectura`, `valor_redondeado` (cuando un valor trae más decimales que su columna; nunca se redondea en silencio).
- Una transacción por archivo: si un valor no cabe en la base, el archivo entero se revierte, no queda marcado y se reintenta en la próxima ingesta.
- Parser: `NaN` e `Infinity` en un monto ahora son `valor_invalido` (`Decimal()` los aceptaba).
- 53 pruebas, 100 % de líneas.

**Qué se aprendió**
- La ida y vuelta por DuckDB conserva exactos los `Decimal` (incluida la tarifa `0.966`) y la hora con su zona `-05:00`.

**Problemas encontrados**
- Ninguno. Pendiente menor: el lector analiza los XML de un archivo antes de saber si su SHA-256 ya estaba ingerido; con carpetas de cientos de documentos no pesa, se revisará si crece.

## 2026-11-20 — M2, paso 1: esquema y base por cliente

**Qué se hizo**
- Plan de M2 acordado: esquema DuckDB, ingesta idempotente por SHA-256 y CUFE, comandos `clientes crear` e `ingerir`.
- Se agregó `duckdb` (dependencia del stack, SPEC §3). `schema.sql` versión 1 con `documentos`, `referencias`, `impuestos`, `retenciones`, `lineas`, `impuestos_linea`, `archivos_ingeridos`, `advertencias`, `cliente` y `schema_version`.
- `base.py`: ubicación por `AUDITOR_DIAN_HOME`, `crear_cliente` (no deja bases a medio crear si falla) y `abrir` (verifica la versión del esquema). El `id_cliente` admite solo dígitos (NIT sin DV o cédula), acordado con el equipo.
- Decisión [0004](decisiones/0004-escala-numerica.md): montos en `DECIMAL(21,6)`, tarifas en `DECIMAL(9,3)`. Se actualizaron `CLAUDE.md` y el SPEC §5.
- Las pruebas usan un `AUDITOR_DIAN_HOME` temporal (`tests/conftest.py`), para no tocar nunca la carpeta real. 41 pruebas.

**Qué se aprendió**
- DuckDB redondea en silencio los decimales que no caben en la columna, y su binding de Python (2.0) no acepta horas con offset negativo; ambas cosas quedaron resueltas en la decisión 0004.
- El paquete instalable incluye `schema.sql` (verificado construyendo el wheel).

**Problemas encontrados**
- Ninguno.

## 2026-11-20 — Cotejo contra el Anexo Técnico

**Qué se hizo**
- Se descargaron los PDF oficiales del Anexo FE 1.9 (753 páginas) y del Anexo de Documento Soporte 1.1 (290 páginas) desde dian.gov.co y se cotejaron todas las rutas del parser. Resultado por campo, con ID de campo y sección: [investigacion/anexo-tecnico.md](investigacion/anexo-tecnico.md).
- `contenedor.py`: un `AttachedDocument` puede traer varias respuestas DIAN (AE38, 1..N); ahora se usa la que corresponde al CUFE del documento. Un código distinto de `02`/`04` (p. ej. un evento `030`) ya no se interpreta como rechazo: queda `validado_dian = None` con advertencia `validacion_codigo_desconocido`. 31 pruebas, 100 % de líneas.
- Comentarios del código actualizados con las referencias del anexo.
- SPEC §7: el informe `retenciones` debe aclarar que son autorretenciones del emisor.

**Qué se aprendió**
- En la versión 1.9 las tablas de códigos (tipos de documento, de identificación, tributos, formas de pago) salieron del anexo y están en la "Caja de Herramientas" de la DIAN. Las rutas se pudieron confirmar; varios valores de códigos no.
- `WithholdingTaxTotal` en factura y documento soporte son **autorretenciones** del emisor (FAT01, DSAT01), no las retenciones que practica el comprador. Cambia la lectura del informe `retenciones`.
- El anexo se contradice sobre la moneda (FAD15 vs. FAD15a, FAR02, FAR04). El fixture de exportación sigue la práctica de la 1.8.

**Problemas encontrados**
- La herramienta de lectura web no abre PDF de más de 10 MB ni extrae texto; se descargaron con `curl` y se leyeron con `pdftotext`. Los PDF no se guardan en el repositorio.
- Pendiente: conseguir la Caja de Herramientas para cotejar las tablas de códigos.

## 2026-11-20 — Cierre de M1 (con salvedad)

**Qué se hizo**
- Se agregó `pytest-cov` (dependencia de desarrollo, [decisión 0003](decisiones/0003-pytest-cov.md)). Tres pruebas nuevas para las ramas sin cubrir: respuesta DIAN sin código, miembro de ZIP corrupto e identificación en `PartyLegalEntity`. 29 pruebas, 100 % de líneas.
- Resumen y métricas en [hitos/M1.md](hitos/M1.md); M1 marcado en el cronograma.
- El paso 6 del plan (robustez) no se hizo aparte: XXE, XML mal formado, raíz desconocida, campos faltantes y ZIP desproporcionados quedaron cubiertos en los pasos 1, 3 y 4.

**Qué se aprendió**
- Medir la cobertura encontró tres ramas reales sin prueba, incluida la del miembro de ZIP corrupto, que sí aparece en correos reales.

**Problemas encontrados**
- **Salvedad del cierre**: M1 se cerró solo con XML sintéticos. Las rutas DIAN siguen sin verificar contra el anexo. La condición para quitar la salvedad (facturas reales de la fase 0 y cotejo del anexo) está en [hitos/M1.md](hitos/M1.md) y debe cumplirse antes de terminar M2.

## 2026-11-20 — M1, paso 5: exportación, contingencia, documento soporte y nota de ajuste

**Qué se hizo**
- Fixtures sintéticos de factura de exportación `02` (USD, TRM 4000, adquirente del exterior), documento soporte `05` (compra a persona natural con CC, ReteRenta y ReteICA) y nota de ajuste `95`. La contingencia `03` se prueba derivándola de la factura `01`, porque su estructura es idéntica.
- Nueva advertencia `campo_faltante: trm` cuando la moneda no es COP y falta `cac:PaymentExchangeRate`. 26 pruebas.

**Qué se aprendió**
- El parser no necesitó cambios para los tipos nuevos: el documento soporte usa la raíz `Invoice` y la nota de ajuste la raíz `CreditNote`; el tipo sale del código. Cubrir ahora el documento soporte (que el cronograma pone en M1 y el SPEC §12 no) costó solo fixtures.
- En el documento soporte el XML lo genera el comprador, pero el vendedor sigue en `AccountingSupplierParty`, así que `emisor` sigue siendo el proveedor. Por verificar contra el anexo del documento soporte.

**Problemas encontrados**
- Pendiente para M3: los montos de documentos en moneda extranjera vienen en esa moneda. Los informes deben convertirlos con la TRM del documento, o separarlos por moneda, antes de sumar con documentos en pesos. Decidirlo al diseñar `compras_por_proveedor`.

## 2026-11-20 — M1, paso 4: lector de ZIP, XML y carpetas

**Qué se hizo**
- `lector.py`: `leer_ruta` recorre un XML, un ZIP o una carpeta (recursiva, en orden alfabético) y entrega una `Lectura` por documento: ruta, SHA-256 del archivo tal como llegó, miembro del ZIP, documento o error.
- Los ZIP se abren en memoria; se ignoran PDF, carpetas y metadatos `__MACOSX/`. Un ZIP sin XML, un ZIP dañado o un XML mal formado quedan como `Lectura` con error y el recorrido sigue.
- Límites contra archivos desproporcionados (zip bomb): 20 MB por XML descomprimido, leído con tope, y 200 MB por ZIP. 21 pruebas.

**Qué se aprendió**
- El SHA-256 es del archivo recibido (el ZIP completo), no de cada XML: así "el mismo archivo no se reprocesa" (SPEC §6) funciona aunque el ZIP traiga varios documentos. Todo archivo produce al menos una `Lectura`, para que M2 lo pueda marcar como procesado aunque no tenga documentos.
- El tamaño declarado en el encabezado de un ZIP puede ser falso; por eso se lee con tope en lugar de confiar en él.

**Problemas encontrados**
- Ninguno. Pendiente: ZIP dentro de ZIP no se recorre; se revisará si aparece en los documentos reales.

## 2026-11-20 — M1, paso 3: AttachedDocument

**Qué se hizo**
- `contenedor.py`: `leer_xml` recibe cualquier XML. Si es un `AttachedDocument`, saca el documento embebido (CDATA) y lee el `ApplicationResponse` para fijar `validado_dian`: `True` con código `02`, `False` con otro código, `None` si no hay respuesta.
- Si la respuesta DIAN trae un CUFE distinto al del documento, no cuenta como validación y queda la advertencia `validacion_de_otro_documento`.
- `tests/fabrica.py` arma contenedores sintéticos alrededor de los fixtures existentes, sin duplicar XML. 17 pruebas.

**Qué se aprendió**
- El documento embebido llega como texto ya decodificado; si conserva su declaración `encoding="ISO-8859-1"`, lxml falla o daña las tildes. Se quita la declaración antes de parsear.

**Problemas encontrados**
- El código `02` ("Documento validado por la DIAN") y las rutas del contenedor siguen por verificar contra el Anexo Técnico.

## 2026-11-20 — Grafo de conocimiento del repositorio

**Qué se hizo**
- Grafo generado en `graphify-out/`: 147 nodos, 255 aristas, 11 comunidades (modelos del parser, alcance del SPEC, parser UBL, documentación, pruebas, CI, CLI, Anexo Técnico, entre otras).
- `CLAUDE.md` ahora indica consultar el grafo antes de explorar. Decisión: [0002](decisiones/0002-grafo-de-conocimiento-en-el-repo.md).

**Qué se aprendió**
- El código se extrae por AST sin costo de tokens; solo los documentos requieren extracción semántica (~66 mil tokens en esta corrida, una vez; luego queda en caché).

**Problemas encontrados**
- Diagnóstico de salud: 13 aristas con extremo colgante y 8 colapsadas (duplicadas entre los mismos nodos). El grafo es usable, pero esas relaciones pueden faltar.

## 2026-11-20 — M1, pasos 1 y 2: factura y notas

**Qué se hizo**
- `modelos.py`: dataclasses inmutables (`Documento`, `Tributo`, `Parte`, `Referencia`, `Linea`, `Advertencia`), con montos en `Decimal`.
- `ubl.py`: lee Invoice, CreditNote y DebitNote mediante una tabla por raíz (elemento de tipo, de línea, de cantidad y de totales).
- Fixtures sintéticos: factura `01`, nota crédito `91` y nota débito `92`. 9 pruebas: campos faltantes y montos inválidos dan advertencia, una raíz desconocida se rechaza y no se resuelven entidades externas (XXE).
- Nota de investigación sobre la versión vigente del anexo: [anexo-tecnico.md](investigacion/anexo-tecnico.md).

**Qué se aprendió**
- DebitNote en UBL 2.1 no tiene elemento de tipo y usa `RequestedMonetaryTotal` en lugar de `LegalMonetaryTotal`.
- Una nota puede referenciar varias facturas, por eso `referencias` es una tupla. Cómo guardarla en DuckDB se decide en M2.
- El prefijo solo viene en las extensiones DIAN de las facturas; `numero` guarda el `cbc:ID` completo.

**Problemas encontrados**
- No se consiguió el PDF del Anexo Técnico 1.9; las rutas propias de la DIAN quedan marcadas "por verificar".

## 2026-11-19 — Estructura inicial del proyecto

**Qué se hizo**
- Proyecto creado con `uv` (paquete `auditor_dian` en `src/`, distribución `auditor-dian-core`, Python ≥ 3.11).
- CLI mínima `auditor --help` con `typer`, una prueba de humo, configuración de `ruff` y CI en GitHub Actions (`ruff` + `pytest`).
- `.gitignore` que excluye datos reales (`data/`, `*.duckdb`, `*.zip`).
- Carpeta `docs/` con `bitacora.md`, `decisiones/`, `hitos/` e `investigacion/`.
- Decisión registrada: [0001 — Estructura del proyecto](decisiones/0001-estructura-del-proyecto.md).

**Qué se aprendió**
- `uv init --package` nombra el módulo igual que la distribución (`auditor_dian_core`); el SPEC pide `auditor_dian`, así que se fijó `module-name` en `[tool.uv.build-backend]`.

**Problemas encontrados**
- Ninguno.
