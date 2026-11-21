<p align="center"><img src="src/auditor_dian/logo.svg" alt="Logo de Auditor DIAN: una factura bajo una lupa" width="112"></p>

# Auditor DIAN

> **No es un producto oficial de la DIAN** ni está afiliado a ella ni respaldado por ella. "DIAN" se usa solo para describir las facturas electrónicas que procesa. Las cifras que produce requieren revisión de un contador.

`auditor-dian-core` es una librería Python + CLI + servidor MCP, local, que convierte las facturas electrónicas DIAN que recibe un cliente en una base de datos consultable y en informes para el contador.

Estado: `core` v0.1 interno (etiqueta `v0.1.0`): parser, base por cliente, seis informes, servidor MCP e interfaz de plugins. El alcance completo está en [`SPEC.md`](SPEC.md) y el plan en [`docs/cronograma.md`](docs/cronograma.md).

![Claude registra un cliente, carga sus facturas de Descargas (deja fuera la que es de otra persona) y responde el IVA del bimestre con los CUFE que lo respaldan](docs/img/demo-claude-code.gif)

*Demostración en Claude Code con facturas sintéticas de las pruebas.*

## Para contadores: usarlo en Claude Desktop

No hace falta saber programar ni contratar un servidor: Auditor DIAN corre en tu propio computador, dentro de Claude Desktop.

1. **Instala [Claude Desktop](https://claude.ai/download)** e inicia sesión.
2. **Instala la extensión**: descarga `auditor-dian-<versión>.mcpb` de la [última versión](https://github.com/RafaGM1108/auditor-dian-core/releases/latest) y ábrelo (doble clic) o, en Claude Desktop, *Configuración → Extensiones → Configuración avanzada → Instalar extensión*. Elige la **carpeta de datos**: ahí se guardan las bases de tus clientes (por defecto `~/.auditor-dian`). Claude Desktop instala lo demás por su cuenta; la primera vez puede tardar un par de minutos.
3. **Descarga las facturas** del correo como siempre: los ZIP quedan en tu carpeta de Descargas.
4. **Escríbele a Claude**: *Carga mis facturas*. Claude revisa tu carpeta de Descargas, mira a qué empresa o persona le vendieron cada factura y te dice cuáles son de clientes que aún no tienes registrados, con su nombre. Respóndele *sí, créalos* y vuelve a pedir *carga mis facturas*. Cada factura queda guardada en su cliente.
   - Si las guardaste en otra carpeta, nómbrala como la ves: *carga las facturas de la carpeta "facturas enero" del Escritorio*. No hace falta escribir rutas.
   - El NIT o la cédula los puedes escribir como quieras: *NIT 900.000.009-0*, *9000000090*, *C.C. 79.123.456*. Auditor DIAN se encarga de quitar el dígito de verificación.
   - Puedes repetir la carga cuantas veces quieras: lo que ya estaba no se duplica.
5. **¿Ya tenías a ese cliente?** Pregunta *¿ya tengo registrada a Mi Cliente SAS?* o *¿qué meses tengo cargados de Mi Cliente SAS?*. Si le pides crear un cliente que ya existe, Claude te muestra lo que ya tiene en vez de crearlo de nuevo.
6. **Pregunta**: *¿Cuánto IVA en compras hubo en el bimestre 1 de 2026?*, *¿qué facturas a crédito llegaron en marzo?*, *exporta las retenciones del primer semestre a un Excel en mi escritorio*.

Qué hace y qué no:

- Todo queda en tu computador. No se conecta a la DIAN ni a otros servicios; Claude solo ve lo que las herramientas le responden en la conversación.
- Nada se borra ni se modifica: cargar solo agrega y exportar crea un Excel nuevo.
- Cada cliente está separado: si cargas en un cliente facturas que no son suyas (ni las compró ni las vendió), no se guardan y Claude te lo dice. Así la información de un cliente no termina en las cifras de otro.
- Las cifras salen de la base, no las calcula el modelo, y vienen con los CUFE que las respaldan. Igual requieren revisión del contador.

### Si algo falla o una cifra no cuadra

Escríbele a Claude *dame el diagnóstico de Auditor DIAN* y copia la respuesta: trae la versión, tus clientes, cuántos documentos hay y las advertencias de lectura, sin montos ni contenido de las facturas. Repórtalo en *Issues* del repositorio (formularios "Algo salió mal" y "Una cifra no cuadra") o a quien te compartió la extensión. Si una cifra no cuadra, di cuál esperabas y de qué documento la sacaste; **no adjuntes facturas reales** en un reporte público.

## Para desarrolladores

```
uv sync
uv run pytest
uv run ruff check .
uv run auditor --help
```

## Uso

```
uv run auditor clientes crear 900000009 --nombre "Cliente SAS"
uv run auditor ingerir 900000009 ~/facturas/          # ZIP, XML o carpeta
uv run auditor informe 900000009 iva_compras_por_bimestre --desde 2026-01-01 --hasta 2026-02-28 --xlsx iva.xlsx
```

Las bases viven en `~/.auditor-dian/` (o en `AUDITOR_DIAN_HOME`).

## Conectar con Claude (MCP)

En Claude Code, desde la carpeta del repositorio:

```
claude mcp add auditor -- uv run --directory "$PWD" auditor mcp
```

En Claude Desktop, en `claude_desktop_config.json`:

```json
{"mcpServers": {"auditor": {"command": "uv", "args": ["run", "--directory", "/ruta/a/auditor-dian-core", "auditor", "mcp"]}}}
```

O como extensión de Claude Desktop, con nombre, descripción y logo propios: `./scripts/empaquetar_mcpb.sh` arma `dist/auditor-dian-<versión>.mcpb` (requiere `uv` y `npx`). En Desktop: Configuración → Extensiones → Configuración avanzada → Instalar extensión, y elegir la carpeta de datos (la de `AUDITOR_DIAN_HOME`). Desktop instala Python y las dependencias con uv.

Para desarrollar, `./scripts/empaquetar_mcpb.sh --desarrollo` arma "Auditor DIAN (desarrollo)", que ejecuta `core` en modo editable desde este repositorio: tras cada cambio basta con desactivar y volver a activar la extensión en Desktop. Solo funciona en la máquina donde se armó. Para incluir plugins en modo editable, se pasan sus repositorios: `./scripts/empaquetar_mcpb.sh --desarrollo ../mi-plugin`.

El servidor abre las bases en solo lectura. Su única herramienta que escribe es `exportar_informe`, que crea un `.xlsx` nuevo y nunca sobrescribe.

## Plugins

Un paquete aparte agrega informes, herramientas MCP o lectores de documentos declarando en su `pyproject.toml`:

```toml
[project.entry-points."auditor_dian.plugins"]
mi_plugin = "mi_paquete:register"
```

`register(app)` recibe la interfaz de `src/auditor_dian/plugins.py`. Hay un ejemplo completo en `tests/plugin_ejemplo.py`.

## Licencia

[MIT](LICENSE).
