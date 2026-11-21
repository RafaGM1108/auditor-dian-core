# 0005 — Esquema de la base por cliente e identificación del cliente

Fecha: 2026-11-20

## Contexto

M2 debía guardar lo que entrega el parser en una base DuckDB por cliente (SPEC §6) y permitir reingerir sin duplicar. Había que decidir cómo partir los datos en tablas, cuál es la llave de idempotencia y cómo se identifica al cliente.

## Decisión

- **Una base por cliente** en `AUDITOR_DIAN_HOME/clientes/<id>/auditor.duckdb` (por defecto `~/.auditor-dian/`). Así se borra o copia un cliente sin tocar a los demás.
- **Esquema versión 1** en `src/auditor_dian/schema.sql`. La tabla `schema_version` guarda la versión; si no coincide con la del programa, `abrir` se detiene con un error claro en vez de leer datos con otro formato.
- **Tablas hijas** para lo que en el modelo es una lista: `referencias` (una nota puede citar varias facturas), `impuestos`, `retenciones`, `lineas` e `impuestos_linea`. Cada fila lleva `cufe` y `orden` como llave.
- **Idempotencia en dos niveles**: el SHA-256 del archivo tal como llegó (`archivos_ingeridos`) y el CUFE (`documentos`). El mismo documento recibido en otro archivo no se duplica; queda la advertencia `cufe_repetido`.
- **Sin CUFE no se guarda**: no habría forma de evitar duplicados. Queda la advertencia `documento_sin_cufe`.
- **Advertencias y errores en una sola tabla** (`advertencias`), con `cufe` vacío cuando no hubo documento. Son trazables al archivo por `sha256` y `miembro`.
- **Una transacción por archivo**: un archivo se guarda completo o no queda registrado y se reintenta.
- **`id_cliente` solo dígitos** (NIT sin DV o cédula), acordado con el equipo. Así se compara exacto con la identificación del adquirente en el XML; si no coincide, el documento se guarda con la advertencia `adquirente_distinto`.

## Alternativas descartadas

- **Una sola base para todos los clientes**: obliga a filtrar por cliente en cada consulta y mezcla datos que deben poder entregarse o borrarse por separado.
- **Listas como JSON en `documentos`**: menos tablas, pero los informes de M3 necesitan sumar impuestos y retenciones con SQL simple.
- **Aceptar el NIT con DV o con puntos y normalizarlo**: más cómodo al escribir, pero esconde errores de digitación; se prefirió rechazar con un mensaje que muestra el formato.
- **Solo el CUFE como llave**: obligaría a abrir y analizar cada archivo en cada ingesta, y no registraría los archivos dañados.

## Consecuencias

- Cambiar el esquema exige subir `VERSION_ESQUEMA` y escribir una migración; por ahora no hay ninguna.
- **Actualización 2026-11-20 — versión 2**: se agregaron a `documentos` las columnas `total_impuestos_incluidos`, `descuentos`, `cargos`, `anticipos` y `redondeo`, porque una factura real traía un cargo global que impedía cuadrar el total. No se escribió migración: solo existían bases de prueba. Una base versión 1 se rechaza con un mensaje claro. Desde que haya bases de usuarios, cada cambio de esquema necesitará su migración.
- Un cliente persona natural con cédula y uno con NIT no se distinguen por el formato del id; se distinguen por la base en que están.
- **Actualización 2026-11-20 — versión 3**: la columna `medio_pago` guardaba en realidad la **forma** de pago (`cbc:ID`, FAN02: contado o crédito); se renombró `forma_pago`. Se agregó `medios_pago VARCHAR[]` con el `PaymentMeansCode` (FAN03) de cada `cac:PaymentMeans`, que es 1..N: en 10 de 57 facturas reales vienen dos medios. Se eligió una lista en la misma tabla y no una tabla aparte porque `PaymentMeans` no trae montos por medio: no hay nada que sumar por separado. Tampoco hubo migración: las únicas bases eran de prueba y la demo sintética, que se reconstruyó. Una base versión 2 se rechaza con un mensaje que pide crear el cliente de nuevo y volver a ingerir. El campo del modelo `Documento` cambió igual (`forma_pago`, `medios_pago`); es parte de la interfaz de plugins, pero aún no hay plugins publicados.
