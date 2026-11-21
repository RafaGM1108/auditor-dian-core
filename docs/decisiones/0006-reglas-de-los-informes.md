# 0006 — Reglas comunes de los informes

Fecha: 2026-11-20

## Contexto

M3 entrega los seis informes del SPEC (§7). Antes de escribirlos había que fijar reglas que todos comparten: cómo se redondea, qué pasa con otras monedas, qué documentos suman o restan, cuándo una nota anula una factura y cómo se arman los periodos. El equipo las aprobó el 2026-11-20.

## Decisión

1. **Redondeo**: SQL suma los valores exactos de la base. Se redondea a 2 decimales, mitad hacia arriba, solo al mostrar (en pantalla con formato colombiano, `400.000,00`). En Excel el valor va exacto con formato `#,##0.00`, para que una suma hecha en Excel dé lo mismo que el informe.
2. **Moneda extranjera**: no se convierte con la TRM (no hay casos reales y la dirección de la TRM en el anexo es ambigua). Cada informe agrupa por moneda y lo dice en su nota.
3. **Signos**: las facturas (`01`, `02`, `03`), el documento soporte (`05`) y las notas débito (`92`) suman. Las notas crédito (`91`) y las notas de ajuste del documento soporte (`95`) restan.
4. **Anulaciones**: una nota crédito anula la factura que referencia (por CUFE, o por número si no trae CUFE). La anulación es **total** si la suma de las notas iguala el total de la factura con la tolerancia de ±2,00 del Anexo FE 1.9 (5.2.1.1); si no, es **parcial**.
5. **`no_validadas`** incluye las que no tienen respuesta de la DIAN y las rechazadas, con una columna `estado`.
6. **IVA**: el informe de IVA usa solo el tributo `01`, por tarifa. Así un impuesto por unidad (como el `22` de bolsas, cuya base es una cantidad) no se suma como base en pesos.
7. **Periodos**: bimestres fijos (enero–febrero, marzo–abril, …) para el IVA y meses para las retenciones, por fecha de emisión.

Además, al implementar el primer informe:

- **Solo cuentan los documentos del cliente**: los que llegaron a nombre de otro adquirente (advertencia `adquirente_distinto`) se guardan, pero no entran en los informes. Un lote real mezclaba facturas de cinco personas.
- **El rango de fechas es inclusivo** y se aplica a la fecha de emisión.
- **Cada informe es SQL puro** en `src/auditor_dian/informes/`: `<nombre>.sql` (detalle) y `<nombre>_resumen.sql` (resumen sobre el detalle). Python solo los ejecuta y presenta.
- **Los informes abren la base en solo lectura** (`abrir(id, solo_lectura=True)`), lo mismo que hará el servidor MCP.

## Alternativas descartadas

- **Redondear en SQL**: el total de un informe ya no coincidiría con la suma de su detalle exacto.
- **Convertir con la TRM**: se haría sin un solo caso real para comprobar la dirección de la conversión.
- **Contar todo lo que hay en la base**: inflaría las compras con facturas de terceros que alguien reenvió.
- **Armar los informes en Python**: contradice la regla de que toda cifra sale de SQL o de código probado y simple.

## Consecuencias

- Cuando aparezca un documento real en otra moneda, se revisa la regla 2 con una nota nueva.
- Un informe nuevo se agrega escribiendo sus dos `.sql` y su nota en `informes/__init__.py`.

- **Actualización 2026-11-20 — tipo `04`**: al cotejar la Caja de Herramientas FE 1.9 (tabla 13.1.3) apareció el tipo `04`, "Factura electrónica de Venta - tipo 04". Suma como las demás facturas (regla 3) y una nota crédito también puede anularla (regla 4).
