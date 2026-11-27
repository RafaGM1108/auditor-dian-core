# 0013 — Nota crédito que cita varias facturas

Fecha: 2026-11-26

## Contexto

Una nota crédito puede citar varias facturas: el modelo lo admite (`referencias` es una tabla aparte, decisión 0005). El informe `duplicados_y_anulaciones` le descontaba a cada factura citada el total completo de la nota. Una nota de 306.000 sobre dos facturas de 150.500 y 155.500 aparecía como si hubiera descontado 306.000 de cada una (612.000 en total), y la clasificación quedaba mal: `anulada_parcial` donde la anulación era total. No había un caso real, pero el defecto estaba anotado desde M3 ([issue #7](https://github.com/RafaGM1108/auditor-dian-core/issues/7)).

La nota no dice cuánto le corresponde a cada factura. El XML trae las facturas en `BillingReference` y las líneas de la nota, pero no un valor por factura.

## Decisión

Lo que cada nota le descuenta a cada factura que cita:

1. **Cita una sola factura**: todo su total, como antes.
2. **Cita varias, todas están cargadas y la nota suma lo mismo que ellas (±2,00)**: cada factura descuenta su propio total. Es el caso de una nota que anula varias facturas completas.
3. **Cualquier otro caso**: el reparto no se sabe. La factura sale como `anulada_sin_repartir`, con `valor_notas` vacío, y el contador decide.

Las facturas citadas se buscan en toda la base del cliente, no solo en el rango del informe: una nota de marzo puede citar una factura de febrero y otra de marzo.

## Alternativas descartadas

- **Repartir en proporción al total de cada factura**: da una cifra que ningún documento respalda, contra la regla de que el modelo y el programa no inventan cifras.
- **Repartir por las líneas de la nota**: las líneas no dicen a qué factura corresponden.
- **Dejarlo como estaba hasta ver un caso real**: el error infla lo anulado, que es justo lo que el contador revisa antes de cerrar un periodo.

## Consecuencias

- `duplicados_y_anulaciones` tiene un hallazgo nuevo, `anulada_sin_repartir`. En el resumen su `valor_notas` suma solo lo que sí se sabe repartir.
- Una nota que cita una factura que todavía no se cargó queda sin repartir hasta que se cargue.
- Una nota que cita dos veces la misma factura cuenta como si citara varias y queda sin repartir: se prefiere pedir revisión a dar una cifra dudosa.
