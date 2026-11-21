# 0004 — Escala numérica en la base: guardar exacto lo que trae el XML

Fecha: 2026-11-20

## Contexto

El SPEC y `CLAUDE.md` fijaban `DECIMAL(18,2)` para todos los montos. Al cotejar el Anexo Técnico FE 1.9 se vio que la DIAN admite **hasta 15 dígitos con 6 decimales** en montos y precios (`PayableAmount` FAU14, `TaxableAmount` FAS05, `PriceAmount` FBB02: formato "1-15 p (0-6)") y **3 decimales** en tarifas (`Percent` FAS14/FAT10: "p (0..3)"). Ya hay casos reales de tarifa con 3 decimales, como ReteICA `0.966`.

Además, una prueba mostró que DuckDB **redondea en silencio** al insertar un `Decimal` con más decimales que la columna (`0.9665` en `DECIMAL(9,3)` queda `0.967`), y rechaza con error los valores que no caben en la parte entera.

## Decisión

- Montos, precios unitarios, cantidades y TRM: `DECIMAL(21,6)` (15 dígitos enteros y 6 decimales).
- Tarifas: `DECIMAL(9,3)`.
- La base guarda exacto lo que trae el XML. El redondeo a 2 decimales se hace solo al presentar (informes de M3).
- Si un valor trae más decimales que su columna, la ingesta lo detecta antes de insertar y deja la advertencia `valor_redondeado`; nunca se redondea en silencio.
- La hora de emisión se guarda en `TIMETZ`. Se inserta como texto ISO con `CAST(? AS TIMETZ)`, porque el binding de Python de DuckDB 2.0 no acepta un `time` con offset negativo (-05:00).

Se actualizaron `CLAUDE.md` (regla de montos) y el SPEC §5.

## Alternativas descartadas

- **`DECIMAL(18,2)` con advertencia al redondear**: más simple, pero los totales podrían diferir del XML por centavos y el informe dejaría de cuadrar exacto con los documentos (SPEC §1, trazabilidad).
- **`DECIMAL(18,6)`**: deja solo 12 dígitos enteros, menos de los 15 que permite el anexo.
- **Guardar montos como texto**: exacto, pero obliga a convertir en cada consulta SQL y pierde la validación de tipo.

## Consecuencias

- Las columnas `DECIMAL(21,6)` usan enteros de 128 bits en DuckDB: algo más lentas que las de 18 dígitos, irrelevante para el volumen de un cliente.
- Los informes deben redondear explícitamente al presentar y decir con qué regla.
