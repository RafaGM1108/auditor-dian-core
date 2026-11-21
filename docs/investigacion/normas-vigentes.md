# Normas vigentes que afectan al proyecto

Consultado el 2026-11-20. El detalle campo por campo del XML está en [anexo-tecnico.md](anexo-tecnico.md).

## Factura electrónica

- **Resolución DIAN 000165 de 2023** (1-nov-2023): sistema de facturación electrónica. Adopta el **Anexo Técnico 1.9**, obligatorio desde el 1-may-2024 (Resolución 000008 de 2024). Es la versión que lee el parser. [1]
- **Resolución DIAN 000202 de 2025** (31-mar-2025, Diario Oficial 53.076 del 1-abr-2025, vigente desde su publicación): modifica en parte la 165 [2].
  - **No cambia el Anexo Técnico ni los campos del XML**: recuerda que la 165 "adopta la versión 1.9 del anexo técnico".
  - Nuevo art. 69: si el comprador pide la factura a su nombre, el vendedor solo puede pedirle nombre, tipo y número de identificación y correo. Si no la pide, no le puede pedir datos. Cuando la DIAN habilite un servicio de consulta (art. 70, sin fecha anunciada), bastará el número de identificación.
  - Reglas para el documento equivalente de servicios públicos (plazo de hasta 48 horas para validar).
- **Resolución DIAN 000227 de 2025** (23-sep-2025, Diario Oficial 53.254): "Resolución Única en Materia Tributaria, Aduanera y Cambiaria" [3]. **Compila** las resoluciones existentes; no las reemplaza en contenido. Su Título 5, "Sistema de facturación", incluye factura electrónica, documento soporte, nómina electrónica y RADIAN. Dice que "todos los anexos contemplados en las resoluciones compiladas ... continuarán vigentes".
  - *Sin verificar*: no leímos completo el Título 5 (la página tiene casi 500.000 caracteres). Falta confirmar que cita los anexos FE 1.9 y DS 1.1 sin cambios. La nota de la Resolución 202 dice que ella quedó "compilada en la Resolución 227 de 2025".

## Recepción: cómo le llegan las facturas al comprador

Según el micrositio de la DIAN [4]:

- El vendedor envía la factura al **correo de recepción** que el comprador registró: "Este correo es obligatorio y exclusivo para recibir documentos electrónicos".
- El correo lleva "un archivo .ZIP" que contiene un **`AttachedDocument`** (contenedor electrónico con la factura y su validación DIAN). El PDF es opcional. Máximo 2 MB por envío.
- "Desaparecen los portales web dispuestos para descargar facturas electrónicas."

**Consecuencia para el proyecto:** el insumo legal y universal de todo comprador es el ZIP del correo, que es justamente lo que `auditor ingerir` lee. No depende de que el cliente tenga token DIAN ni software contable.

## Documento soporte

- **Resolución DIAN 000167 de 2021**: documento soporte en adquisiciones a sujetos no obligados a facturar, con su anexo técnico (versión 1.1 la que usa el parser). Modificada por la Resolución 000488 de 2022 [5]. Compilada en el Título 5, capítulo 2, de la Resolución 227 de 2025 [3].
- No hay una caja de herramientas pública con XML de ejemplo del documento soporte (búsqueda del 2026-11-20).

## Renta de personas naturales (relevante para `pro`)

- **Deducción del 1 % de las compras** con factura electrónica: art. 336 num. 5 del Estatuto Tributario, agregado por la Ley 2277 de 2022. Tope de 240 UVT. Exige que la factura identifique al comprador y que el pago sea con tarjeta débito, crédito u otro medio electrónico [6].
- UVT 2026: $52.374 (art. 1.2.1 de la Resolución 227 de 2025, según la Resolución 238 de 2025) [3]. Tope de la deducción en 2026: 240 × 52.374 = $12.569.760.

## Fuentes

1. DIAN, Resolución 000165 de 2023, normograma. https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0165_2023.htm
2. DIAN, Resolución 000202 de 2025, normograma. https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0202_2025.htm
3. DIAN, Resolución 000227 de 2025, normograma. https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0227_2025.htm
4. DIAN, micrositio del Sistema de Facturación Electrónica, "Presentación recepción de facturas electrónicas" (sin fecha). https://micrositios.dian.gov.co/sistema-de-facturacion-electronica/presentacion-recepcion-de-facturas-electronica/
5. DIAN, Resolución 000167 de 2021, normograma. https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0167_2021.htm
6. DIAN, Comunicado de prensa 021 de 2024. https://www.dian.gov.co/Prensa/Paginas/NG-Comunicado-de-Prensa-021-2024.aspx ; INCP, "Facturación electrónica: ¿pensando en deducir el 1 % del valor de sus compras en su declaración de renta?", abr-2024. https://incp.org.co/publicaciones/infoincp-publicaciones/impuestos/2024/04/facturacion-electronica-pensando-en-deducir-el-1-del-valor-de-sus-compras-en-su-declaracion-de-renta/
