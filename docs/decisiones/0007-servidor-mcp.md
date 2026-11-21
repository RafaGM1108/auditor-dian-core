# 0007 — Servidor MCP

Fecha: 2026-11-20

## Contexto

M4 entrega el servidor MCP por stdio con las seis herramientas de SPEC §10. Al implementarlo había que decidir qué versión del SDK usar, cuándo abrir la base, cómo entregar los montos a un modelo de lenguaje y qué tanto puede escribir la herramienta `exportar_informe`.

## Decisión

- **SDK oficial `mcp` 2.3**, el que nombra el SPEC. En la versión 2, `FastMCP` pasó a llamarse `MCPServer`; se usa ese nombre.
- **Una conexión de solo lectura por llamada**: cada herramienta abre la base del cliente y la cierra al responder. DuckDB no deja escribir en una base mientras otro proceso la tiene abierta, así que una conexión permanente bloquearía `auditor ingerir` mientras el agente esté conectado.
- **Montos como texto decimal exacto** (`"40500"`, `"150500.123456"`), nunca como número JSON: un float podría alterar centavos.
- **`resumen_periodo` entrega cada cifra ya sumada**: compras total y por tipo, IVA total y por tarifa, retenciones por código, cada una con sus CUFE. Así el agente cita una cifra y no la calcula (regla del proyecto). Las instrucciones del servidor le piden no sumar ni redondear.
- **`buscar_documentos`** solo ve los documentos a nombre del cliente, como los informes (decisión 0006). Devuelve hasta 200 filas más el total de coincidencias.
- **`exportar_informe` solo crea archivos nuevos**: la ruta debe ser absoluta, terminar en `.xlsx`, tener la carpeta creada y no existir. Un agente no puede sobrescribir nada.
- **Errores esperados como `ToolError`** (cliente inexistente, rango invertido, informe desconocido): el agente recibe el mensaje. Cualquier otro error le llega como un error genérico.
- **Aviso del SPEC en cada respuesta**, en el campo `aviso`.

## Alternativas descartadas

- **`mcp<2` con `FastMCP`**: es la API de los ejemplos más comunes, pero quedaría atada a una versión que dejó de evolucionar.
- **Conexión abierta durante toda la sesión**: más rápida, pero impide ingerir mientras el agente está conectado.
- **Montos como números JSON**: más cómodos para el cliente, pero pierden exactitud.
- **Dejar que el agente sume las filas de `buscar_documentos`**: contradice la regla de que el modelo nunca calcula cifras.

## Consecuencias

- Cada llamada abre la base, lo que cuesta unos milisegundos; irrelevante con miles de documentos.
- Si una ingesta está escribiendo justo cuando llega una llamada, esa llamada falla y el agente puede reintentar.

- **Actualización 2026-11-20 — presentación**: el servidor se presenta con título "Auditor DIAN", un resumen de lo que hace, la versión del paquete y el logo como ícono (PNG de 256 px y SVG), según los campos `title`, `description`, `version` e `icons` de la información del servidor en MCP. Los íconos van embebidos como `data:` URI para no depender de red ni de una URL pública. Que el cliente los muestre depende del cliente.
- **Actualización 2026-11-20 — extensión `.mcpb`**: como la página de plugins de Claude Desktop no muestra el título, la descripción ni el ícono que declara el servidor, se agregó un paquete de extensión (manifiesto 0.4 en `mcpb/`, armado por `scripts/empaquetar_mcpb.sh` con `@anthropic-ai/mcpb` 2.1.2). Es de tipo `uv`: lleva el wheel de `core` y un `pyproject.toml` que lo apunta, y Desktop instala Python y las dependencias por su cuenta. Se descartó el tipo `python`, porque exige empaquetar dependencias compiladas (duckdb, lxml, pydantic) por plataforma. La carpeta de datos se pide al instalar (`user_config` de tipo `directory`) y llega como `AUDITOR_DIAN_HOME`. Hay que reconstruir el paquete con cada versión: no sigue al repositorio como la configuración manual.
- **Actualización 2026-11-20 — extensión de desarrollo**: `empaquetar_mcpb.sh --desarrollo` arma una variante cuyo `pyproject.toml` apunta a este repositorio en modo editable (`editable = true`, ruta absoluta) en lugar de llevar el wheel. Desktop sigue mostrando nombre y logo, y el código es siempre el del repositorio: basta con reiniciar el servidor (desactivar y activar la extensión). No es distribuible.

- **Actualización 2026-11-20 — plugins en modo desarrollo**: `--desarrollo RUTA...` instala además, en modo editable, cada plugin cuyo repositorio se indique, para ver sus herramientas en Desktop. El paquete normal sigue llevando solo core: un plugin con otra licencia no se empaqueta en la extensión MIT.
