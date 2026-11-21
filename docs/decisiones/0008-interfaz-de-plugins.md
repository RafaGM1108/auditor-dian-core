# 0008 — Interfaz de plugins

Fecha: 2026-11-20

## Contexto

SPEC §8 fija la frontera con `pro`: `core` busca plugins en el grupo de entry points `auditor_dian.plugins` y a cada uno le pasa un `app` con cuatro capacidades (herramientas MCP, informes, lectores de documentos y abrir la base en solo lectura). Faltaba decidir la forma concreta de esa interfaz, qué pasa cuando un plugin falla y si un plugin puede reemplazar algo de `core`.

## Decisión

- **`App` con cuatro métodos y nada más** (`src/auditor_dian/plugins.py`): `herramienta(funcion)`, `informe(nombre, nota, detalle_sql, resumen_sql)`, `lector(raiz, leer)` y `abrir(id_cliente)`.
- **Los informes de un plugin siguen las reglas de los de core** (decisión 0006): el detalle lee de `docs`, que ya trae solo los documentos del cliente en el rango y el `signo`, y el resumen lee de `detalle`. Se entregan como texto SQL, no como archivos.
- **Las herramientas de un plugin son de solo lectura**: se registran con la misma anotación que las de core y abren la base con `app.abrir`.
- **Un lector de plugin atiende solo raíces XML que core no conoce.** Si falla, su error queda como error de lectura de ese archivo y la ingesta sigue.
- **Nada de core se puede reemplazar**: un nombre de informe o de herramienta, o una raíz, que ya existan se rechazan con `ValueError`. El SDK de MCP, ante un nombre repetido, solo avisa en el log y conserva el primero; por eso se revisa antes.
- **Un plugin que falla al cargar se reporta en stderr y se salta**: `core` sigue completo (SPEC §8). Los plugins se cargan una sola vez, al empezar cualquier comando de la CLI, antes de arrancar el servidor MCP.
- **El plugin de ejemplo vive en `tests/`** (`plugin_ejemplo.py`) y las pruebas lo registran como entry point simulado.

## Alternativas descartadas

- **Pasar al plugin el servidor MCP o la conexión de escritura**: más poder, pero rompe el solo lectura y ata a `pro` a los detalles internos de `core`.
- **Dejar que un plugin reemplace un informe de core**: útil para personalizar, pero un mismo comando daría cifras distintas según lo instalado.
- **Detener la CLI si un plugin falla**: un error en `pro` dejaría inservible a `core`.

## Consecuencias

- Ampliar `App` es un cambio de la frontera con `pro`: se hace solo cuando `pro` lo necesite y con una nota nueva.
- La carga de plugins usa `anyio.run` para listar las herramientas ya registradas, así que debe ocurrir fuera de un bucle asíncrono (como ocurre en la CLI).

- **Actualización 2026-11-20 — abrir para escribir**: `pro` necesita guardar documentos que lee (la exógena) en la base del cliente, en tablas propias `pro_*`. `app.abrir(id_cliente, escritura=True)` abre la base para escribir; está pensado para comandos de carga del plugin (como `auditor ingerir` en core) y no para herramientas MCP, que siguen en solo lectura. Se prefirió esto a que `pro` importe `auditor_dian.base` por su cuenta, porque así todo lo que `pro` toca de `core` sigue pasando por `App`.

- **Actualización 2026-11-20 — nombres que acepta la API de Claude**: Claude Desktop descartó en silencio las herramientas de `pro` porque su parámetro se llamaba `año`; la API de Claude solo acepta nombres de herramienta `[a-zA-Z0-9_-]{1,64}` y de parámetro `[a-zA-Z0-9_.-]{1,64}`. `App.herramienta` ahora verifica el esquema ya generado (incluidos parámetros anidados) y rechaza la herramienta con un mensaje que propone el nombre ASCII; una prueba de core aplica la misma regla a sus propias herramientas. Los nombres de dominio en español siguen valiendo dentro del código y de la base (`año` como columna), no en la interfaz MCP.
