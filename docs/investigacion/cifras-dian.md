# Cifras de facturación electrónica en Colombia

Consultado el 2026-11-20. Cada cifra lleva su fuente y su fecha de corte; si la fuente no da corte, se dice.

## Volumen

| Cifra | Valor | Corte | Fuente |
| --- | --- | --- | --- |
| Facturas electrónicas emitidas al año | 819,7 millones (2020); 1.555,5 millones (2021); 1.907,2 millones (2022); 2.326,8 millones (2023) | Año calendario | Actualícese, 20-mar-2024, con cifras del Comunicado DIAN 016-2024 [1] |
| Crecimiento enero–febrero | 338,9 millones (2023) → 477,2 millones (2024), +41 % | Primer bimestre | Ídem [1] |
| Facturas emitidas en 2024 | "más de 3.103 millones" | Parcial de 2024, sin fecha exacta | Infobae, 12-dic-2024 (prensa, sin verificar en la DIAN) [2] |

Orden de magnitud: más de **6 millones de facturas al día**. Cada una llega al comprador como un ZIP con un `AttachedDocument` (ver "Recepción" más abajo).

## Facturadores

| Cifra | Valor | Corte | Fuente |
| --- | --- | --- | --- |
| Facturadores electrónicos habilitados | 1.143.000, de los que 181.000 se sumaron en el último año | Primer bimestre de 2024 | Actualícese [1] |
| Facturadores electrónicos habilitados | 1.160.845; esperados 1.300.000 | Abril de 2024 (sin día exacto para el total nacional) | Comunicado de prensa DIAN 021, 18-abr-2024 [3] |
| Habilitaciones por mes en factura electrónica | Entre 11.000 y 27.000 al mes; suman 183.777 (2023), 221.234 (2024), 191.476 (2025) y 132.859 (enero–septiembre de 2026) | 30-sep-2026 | Micrositio DIAN "Consolidado cifras SFE" [4]. La página no rotula si son altas nuevas o acumuladas; por el tamaño, frente a 1,16 millones de habilitados, son altas del mes. Las sumas son nuestras. |
| Proveedores tecnológicos habilitados | 97 (56 en Bogotá) | 31-ago-2026 | Ídem [4] (suma nuestra) |

El micrositio [4] no publica el total de habilitados ni el número de documentos validados por año: solo las series mensuales.

## Calidad de las facturas que reciben las personas naturales

Del Comunicado DIAN 021 del 18-abr-2024 [3]:

- En 2023 se expidieron **1.672.392.125** facturas electrónicas a personas naturales.
- Solo **329.673.884 (19,7 %)** sirven para la deducción del 1 % en renta (art. 336 num. 5 del Estatuto Tributario, Ley 2277 de 2022), porque solo esas informan como medio de pago una tarjeta u otro medio electrónico.
- La DIAN recibió quejas de comercios que reportan "la factura como si el pago hubiera sido en efectivo".

Para este proyecto significa que el comprador (o su contador) necesita revisar factura por factura el medio de pago para saber cuánto puede deducir. Es una pregunta que hoy no responde ningún informe de `core` (ver "Ideas" en [herramientas-existentes.md](herramientas-existentes.md)).

## RADIAN (facturas como título valor)

| Corte | Facturas inscritas | Valor (billones) |
| --- | --- | --- |
| 31-dic-2023 | 1.791.902 | 35,5 |
| 31-dic-2024 | 1.869.138 | 43,85 |
| 31-dic-2025 | 1.766.898 | 48,1 |
| 30-sep-2026 | 1.377.240 | 49,5 (acumulado del año en curso) |

Fuente: [4]. Es una fracción mínima del total de facturas, pero cada una de esas exige que el comprador emita eventos (acuse, recibo, aceptación), que `core` todavía no lee (SPEC, fuera de alcance).

## Contadores

- **334.685** contadores públicos activos con tarjeta profesional y **4.665** sociedades de servicios contables, a junio de 2025, según la rendición de cuentas de la Junta Central de Contadores reseñada por el INCP [5].
- Con 2.300 millones de facturas al año (2023), son unas **7.000 facturas por contador al año** si se repartieran parejo. Es un cálculo nuestro e ilustrativo: muchas facturas van a consumidores que no llevan contabilidad.
- Un artículo patrocinado por Alegra pone como caso típico "revisar 200 o 300 facturas al mes" por cliente [6].

## Fuentes

1. Actualícese, "Dian presentó resultados de facturación electrónica; van 1.143.000 facturadores en el país", actualizado el 20-mar-2024. https://actualicese.com/dian-presento-resultados-de-facturacion-electronica-van-1-143-000-facturadores-en-el-pais/
2. Infobae, "La Dian intensifica control sobre facturación electrónica tras detectar irregularidades que suman $2,1 billones", 12-dic-2024. https://www.infobae.com/colombia/2024/12/12/la-dian-intensifica-control-sobre-facturacion-electronica-tras-detectar-irregularidades-que-suman-21-billones/
3. DIAN, Comunicado de prensa 021 de 2024, 18-abr-2024. https://www.dian.gov.co/Prensa/Paginas/NG-Comunicado-de-Prensa-021-2024.aspx
4. DIAN, micrositio del Sistema de Facturación Electrónica, "Consolidado cifras SFE" (sin fecha de publicación; cortes al 30-sep-2026 y al 31-ago-2026). https://micrositios.dian.gov.co/sistema-de-facturacion-electronica/consolidado-cifras-sfe/
5. INCP, "Junta Central de Contadores presenta informe su rendición de cuentas de 2024 y 2025", sep-2025. https://incp.org.co/publicaciones/2025/09/junta-central-de-contadores-presenta-informe-su-rendicion-de-cuentas-de-2024-y-2025/
6. Siempre al Día (patrocinado por Alegra), "Facturas y documento equivalente con IA: ¿cómo revisarlos sin Excel?", actualizado el 18-jun-2026. https://siemprealdia.co/colombia/contabilidad/revisar-facturas-con-ia-y-documento-equivalente/
