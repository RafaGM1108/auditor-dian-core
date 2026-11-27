# SPEC — auditor-dian-core

> Repositorio: `auditor-dian-core` (privado al inicio, público cuando sea estable).
> Versión del spec: 0.1 — 2026-11-19

## 1. Qué es

Librería Python + CLI + servidor MCP, local, que convierte las facturas electrónicas DIAN que recibe un cliente en una base de datos consultable y en informes para el contador.

Principios innegociables:

1. **El modelo de lenguaje nunca calcula.** Toda cifra sale de código determinístico (parser + SQL). Las herramientas MCP devuelven resultados ya calculados.
2. **Trazabilidad.** Todo total se puede desglosar hasta los documentos (CUFE/CUDE) que lo componen.
3. **Solo lectura frente a la DIAN.** No emite, no firma, no envía nada, no genera eventos.
4. **Local y privado.** Sin llamadas de red. Los datos de clientes nunca se suben al repositorio.
5. **Cada cliente, aislado.** Un documento solo entra en un cliente si su identificación interna lo vincula (comprador o vendedor; titular en pro), y se vuelve a verificar al abrir y al consultar (decisión 0011).
6. **`core` no depende de `pro`.** Las extensiones se cargan por plugins (ver §8).

## 2. Fuera de alcance (v0.1)

Emitir o firmar documentos, consultar servicios de la DIAN, eventos RADIAN, declaración de renta, certificados bancarios/ingresos/exógena, OCR de PDFs, nube, multiusuario, interfaz web. Todo eso es `pro` o versiones futuras.

## 3. Stack

- Python 3.11+, gestionado con `uv`
- `lxml` (XML), `duckdb` (base local), `openpyxl` (Excel), `mcp` (SDK oficial, FastMCP), `typer` (CLI), `pytest`
- Sin más dependencias salvo justificación escrita en el PR.

## 4. Entradas soportadas

| Entrada | Detalle |
| --- | --- |
| ZIP | El que llega por correo: contiene XML (+ PDF que se ignora). Puede traer varios XML. |
| `AttachedDocument` | Contenedor DIAN: el documento original va embebido como texto (CDATA) dentro de `cac:Attachment/cac:ExternalReference/cbc:Description`; el resultado de validación DIAN va en un `ApplicationResponse` embebido en `cac:ParentDocumentLineReference`. |
| XML directo | `Invoice`, `CreditNote`, `DebitNote` sin contenedor. |
| Carpeta | Recorre recursivamente ZIP y XML. |

Tipos de documento (código DIAN): `01` factura de venta, `02` exportación, `03` instrumento de transmisión (factura de talonario, contingencia), `04` factura tipo 04, `91` nota crédito, `92` nota débito, `05` documento soporte, `95` nota de ajuste a documento soporte.

> Todos los códigos y rutas XPath deben verificarse contra el **Anexo Técnico de Factura Electrónica vigente** antes de cerrar el parser. Si un campo no aparece, se guarda `NULL` y se registra advertencia; nunca se inventa.

## 5. Campos a extraer

**Documento**: tipo, prefijo, número, CUFE/CUDE (`cbc:UUID`), fecha y hora de emisión, fecha de vencimiento (`cbc:DueDate` o `cac:PaymentMeans/cbc:PaymentDueDate`), forma de pago (`cac:PaymentMeans/cbc:ID`: `1` contado, `2` crédito), medios de pago (`cbc:PaymentMeansCode` de cada `cac:PaymentMeans`, que puede repetirse: `10` efectivo, `48` tarjeta crédito, `49` tarjeta débito...), moneda, TRM si aplica, emisor (NIT, DV, razón social), adquirente (tipo y número de identificación, nombre), subtotal (`LineExtensionAmount`), base gravable (`TaxExclusiveAmount`), total con impuestos (`TaxInclusiveAmount`), descuentos, cargos y anticipos globales (`AllowanceTotalAmount`, `ChargeTotalAmount`, `PrepaidAmount`), redondeo (`PayableRoundingAmount`), total a pagar (`PayableAmount`), documento referenciado (`cac:BillingReference`, para notas), validado por DIAN (sí/no/desconocido, desde el `AttachedDocument`).

**Impuestos** (`cac:TaxTotal`): por cada subtotal → código (`01` IVA, `04` INC, `03` ICA, otros), tarifa, base, valor.

**Retenciones** (`cac:WithholdingTaxTotal`): código (`05` ReteIVA, `06` ReteRenta, `07` ReteICA), tarifa, base, valor.

**Líneas**: número, descripción, cantidad, unidad, valor unitario, valor total, impuestos de la línea.

**Ingesta**: ruta original, SHA-256 del archivo, fecha de ingesta, advertencias.

Montos, precios, cantidades y TRM en `DECIMAL(21,6)`; tarifas en `DECIMAL(9,3)`; nunca `float`. Se guarda exacto lo que trae el XML (la DIAN admite hasta 6 decimales en montos y 3 en tarifas) y se redondea solo al presentar informes. Ver `docs/decisiones/0004-escala-numerica.md`.

## 6. Almacenamiento

- Un archivo DuckDB **por cliente**: `~/.auditor-dian/clientes/<id_cliente>/auditor.duckdb` (ruta configurable con variable `AUDITOR_DIAN_HOME`).
- Tablas: `documentos`, `impuestos`, `retenciones`, `lineas`, `archivos_ingeridos`.
- Esquema en `src/auditor_dian/schema.sql`, versionado con una tabla `schema_version`.
- **Idempotencia**: el mismo CUFE no se inserta dos veces; el mismo archivo (SHA-256) no se reprocesa.
- El cliente se identifica por el NIT/cédula del adquirente. Si un documento no corresponde al cliente que se está cargando, se guarda con advertencia (`adquirente_distinto`).

## 7. Informes (SQL puro en `src/auditor_dian/informes/`)

| Informe | Definición |
| --- | --- |
| `compras_por_proveedor` | Totales por NIT emisor en un rango de fechas; notas crédito restan, notas débito suman. |
| `iva_compras_por_bimestre` | IVA facturado en compras por bimestre, neto de notas. **Es el IVA que aparece en documentos, no una determinación de IVA descontable** (eso lo decide el contador). |
| `retenciones` | Retenciones que figuran en los documentos, por tipo y periodo. En facturas y documento soporte son **autorretenciones declaradas por el emisor** (`WithholdingTaxTotal`; Anexo FE 1.9 FAT01, Anexo DS 1.1 DSAT01), no las retenciones que practica el cliente; el informe debe decirlo. |
| `duplicados_y_anulaciones` | Mismo emisor+número con distinto CUFE; facturas anuladas total o parcialmente por notas crédito; `anulada_sin_repartir` si una nota cita varias facturas y no se sabe cuánto le toca a cada una (decisión 0013, *2026-11-26*). |
| `facturas_credito` | Documentos con forma de pago crédito (`PaymentMeans/ID` = `2`). La fecha de vencimiento se muestra pero no decide: hay emisores que la ponen en ventas de contado. Columna `eventos`: `"por verificar"` (core no consulta la DIAN). |
| `no_validadas` | Documentos sin respuesta de validación DIAN en el contenedor. |

Cada informe devuelve filas con las columnas de detalle (incluido CUFE) y un resumen. Exportable a `.xlsx` (hoja `resumen` + hoja `detalle`).

## 8. Extensiones (frontera con `pro`)

- `core` busca plugins en el grupo de entry points `auditor_dian.plugins`.
- Cada plugin expone `register(app)` donde `app` da acceso a: registrar herramientas MCP, registrar informes, registrar lectores de nuevos tipos de documento, y abrir la base del cliente en solo lectura. En código: `app.herramienta(funcion)`, `app.informe(nombre, nota, detalle_sql, resumen_sql)`, `app.lector(raiz, leer)` y `app.abrir(id_cliente, escritura=False)` (`src/auditor_dian/plugins.py`). `escritura=True` es solo para los comandos de carga del plugin, que escriben en sus propias tablas (`pro_*`); las herramientas MCP siguen siendo de solo lectura.
- Un plugin no puede reemplazar lo de `core`: un nombre de informe o de herramienta, o una raíz XML, que ya existan se rechazan.
- `core` funciona completo sin ningún plugin instalado.
- Mantener esta interfaz mínima; ampliarla solo cuando `pro` lo necesite de verdad.

## 9. CLI

```
auditor clientes crear <id_cliente> --nombre "..."
auditor ingerir <id_cliente> <ruta>           # archivo ZIP/XML o carpeta
auditor informe <id_cliente> <informe> --desde 2026-01-01 --hasta 2026-02-28 [--xlsx salida.xlsx]
auditor mcp                                    # inicia el servidor MCP por stdio
```

## 10. Servidor MCP (stdio)

Las consultas abren la base en modo solo lectura. Las herramientas de carga (`crear_cliente`, `ingerir_facturas`) escriben, pero solo agregan: no borran ni modifican nada (decisión 0010, *cambiado el 2026-11-20*: antes la carga era solo por CLI). Herramientas:

| Herramienta | Entrada | Salida |
| --- | --- | --- |
| `listar_clientes` | buscar (parte del NIT o del nombre, opcional) | id y nombre |
| `historial_cliente` | cliente | nombre, fecha de registro, documentos por tipo y por mes de emisión, cargas por día |
| `buscar_documentos` | cliente, filtros (emisor, fechas, valor mín/máx, tipo, CUFE) | filas + total de coincidencias (máx. 200 filas) |
| `resumen_periodo` | cliente, desde, hasta | totales de compras, IVA, retenciones, conteos por tipo, con CUFEs |
| `facturas_credito` | cliente, desde, hasta | filas con estado de eventos "por verificar" |
| `duplicados_y_anulaciones` | cliente, desde, hasta | filas |
| `compras_por_proveedor` | cliente, desde, hasta | totales por NIT emisor ya sumados + detalle con CUFE (*agregada el 2026-11-26*) |
| `iva_compras_por_bimestre` | cliente, desde, hasta | IVA por bimestre y tarifa ya sumado + detalle con CUFE (*agregada el 2026-11-26*) |
| `no_validadas` | cliente, desde, hasta | documentos sin respuesta DIAN o rechazados, con su archivo (*agregada el 2026-11-26*) |
| `exportar_informe` | cliente, informe, desde, hasta, ruta | ruta del `.xlsx` generado |
| `crear_cliente` | cliente (NIT o cédula como lo escriba el usuario; se guarda sin DV), nombre | ruta de la base creada; si ya existía, su historial sin cambiar nada; aviso si otro cliente tiene el mismo nombre |
| `ingerir_facturas` | cliente, ruta (ZIP, XML o carpeta; completa o como la nombra el usuario, p. ej. "Descargas/facturas enero") | archivos y documentos cargados, advertencias, errores |
| `ingerir_por_cliente` | ruta opcional (sin ella, la carpeta de Descargas) | por cliente: lo cargado; compradores sin cliente creado; archivos sin asignar con su motivo |
| `diagnostico` | — | versión, carpeta de datos, plugins y, por cliente, conteos y advertencias de lectura, sin montos |

Prompts (*agregados el 2026-11-26*): `cargar_facturas` (carpeta opcional), `cerrar_bimestre` (cliente, año, bimestre 1–6; el periodo lo calcula el código) y `revisar_proveedor` (cliente, proveedor, desde, hasta). Solo arman la petición; las cifras salen de las herramientas.

Además de stdio, `auditor mcp --http` sirve las mismas herramientas por Streamable HTTP solo en `127.0.0.1`, en `/mcp/<token>`, para exponerlas con un túnel a claude.ai y al celular sin sacar las bases del equipo (decisión 0014, *agregado el 2026-11-26*).

Cada respuesta incluye el texto: *"Cifras calculadas a partir de los documentos cargados. Requiere revisión del contador."*

## 11. Calidad y pruebas

- Fixtures **sintéticos o anonimizados** en `tests/fixtures/` (NIT ficticios, nombres genéricos). Nunca datos reales.
- `data/`, `*.duckdb`, `*.zip` reales en `.gitignore`.
- Pruebas mínimas: parser por cada tipo de documento; `AttachedDocument` con y sin validación; ZIP con varios XML; idempotencia; cada informe contra valores esperados escritos a mano; las consultas MCP abren la base en solo lectura y la carga por MCP no duplica.
- CI con GitHub Actions: `uv run pytest` y `ruff`.

## 12. Hitos

1. **M1 — Parser**: ZIP + `AttachedDocument` + Invoice/CreditNote/DebitNote, incluidos documento soporte (`05`) y nota de ajuste (`95`) → objetos Python, con pruebas.
2. **M2 — Base y CLI**: esquema DuckDB, ingesta idempotente, `auditor ingerir`.
3. **M3 — Informes**: los seis informes + exportación a Excel.
4. **M4 — MCP**: servidor stdio con las seis herramientas; probado en Claude Desktop/Claude Code.
5. **M5 — Plugins**: entry points y un plugin de ejemplo en `tests/`.

## 13. Criterios de aceptación de v0.1

- Ingerir una carpeta con 50 documentos reales anonimizados sin errores no explicados.
- El total de cada documento real coincide con el del PDF que trae su ZIP (cotejo automático `scripts/cotejar_pdf.py`), salvo diferencias de redondeo del PDF o PDF sin texto, explicadas; y las sumas de `compras_por_proveedor` coinciden con valores escritos a mano en las pruebas. *Cambiado el 2026-11-20: antes pedía una revisión manual en Excel de al menos 10 documentos.*
- Reingerir la misma carpeta no duplica nada.
- Un agente vía MCP responde "¿cuánto IVA facturado en compras hubo en el bimestre 1?" con la cifra exacta y su lista de CUFEs.

## 14. Decisiones de publicación

- Licencia: **MIT** (decidido el 2026-11-20, decisión 0009).
- Nombre público: **Auditor DIAN**; el paquete sigue siendo `auditor-dian-core` y el comando `auditor`. El README aclara que no es un producto oficial de la DIAN ni está afiliado a ella. Logo propio en `src/auditor_dian/logo.svg` (y `logo.png`), que el servidor MCP muestra como ícono, sin símbolos ni colores de la DIAN.
