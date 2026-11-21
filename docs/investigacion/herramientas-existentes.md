# Herramientas existentes para contadores y qué no resuelven

Consultado el 2026-11-20. Las descripciones salen de las páginas de cada producto o de artículos patrocinados por sus fabricantes; no se probaron.

## Lo que hay

| Herramienta | Qué hace | De dónde saca los datos | Requisitos y costo |
| --- | --- | --- | --- |
| **Procesador / Descargador XML FE** (Consultor Contable) [1] | Extensión de Chrome o Edge que descarga las facturas emitidas y recibidas de un período y arma un Excel con "más de 65 datos" por documento (ítems, bases, tarifas). Opcionalmente baja XML y PDF. | Se conecta al módulo de facturación de la DIAN con el **token DIAN** del contribuyente. | $249.000 al año, 2 computadores. Funciona mejor si el usuario está habilitado como facturador en la solución gratuita de la DIAN. 0,6–1 s por documento. |
| **Causación automática DIAN** (Siigo Nube) [2] | Bandeja que trae las compras reportadas a la DIAN, marca cada una como registrada, pendiente o en revisión, ayuda a causarlas con reglas por proveedor, guarda XML y CUFE, y sigue los eventos RADIAN. | **Token DIAN**; si falla, el Excel descargado de la DIAN. | Clientes de Siigo Nube. "No toma decisiones contables por su cuenta." |
| **MCP de Alegra** [3] | Conecta asistentes de IA (Claude, ChatGPT, Perplexity) a la contabilidad del cliente en Alegra, en solo lectura, para revisar facturas y cerrar el mes. | Los datos que ya están en **Alegra Contabilidad**. "La IA no accede a el RADIAN ni el portal DIAN." | Clientes de Alegra. |
| **Lector de eventos / Verificador de terceros** (Accounter) [4] | Extensiones de navegador que revisan los eventos RADIAN de las compras (para deducibilidad) y consultan masivamente si los terceros son facturadores. | Portal DIAN. | Producto de un tercero distribuido por Accounter. |
| **Consulta de facturas de la DIAN para personas naturales** [5] | Desde el 1-ago-2025 la DIAN muestra a cada persona natural las facturas de 2024 a su nombre, para calcular la deducción del 1 % en el formulario 210. | La DIAN. | Gratis; solo para el propio contribuyente. |

## Qué no resuelven (y dónde entra Auditor DIAN)

Análisis propio a partir de lo anterior:

1. **Dependen del token DIAN o de un software contable.** El token llega al correo del contribuyente registrado en el RUT. Un contador con 30 clientes necesita 30 tokens vigentes, o que todos usen el mismo software contable. El ZIP que llega al correo de recepción es el insumo que **todo** comprador tiene por ley ([normas-vigentes.md](normas-vigentes.md)), y es lo que lee `core`.
2. **Entregan datos, no hallazgos.** El Excel de 65 columnas sigue exigiendo que el contador busque a mano duplicados, notas crédito que anulan facturas, ventas a crédito o documentos sin validar. `core` trae esos seis informes ya armados.
3. **La IA conectada a un software contable responde sobre lo ya causado.** El MCP de Alegra ve la contabilidad, no el XML recibido. Lo que llegó y nadie causó no existe para él. El MCP de `core` responde sobre los documentos recibidos, cada cifra con sus CUFE.
4. **Los datos salen del equipo.** Siigo y Alegra son en la nube; la extensión de Consultor Contable no dice dónde procesa. `core` es local y de solo lectura, sin llamadas de red.
5. **La consulta de la DIAN no sirve al contador**: es por contribuyente y solo para la deducción.

**Lo que ellos hacen y `core` no:** causar en un software contable, consultar el portal DIAN, emitir eventos RADIAN y descargar sin correo. El SPEC deja todo eso fuera de alcance.

## Ideas que salen de la investigación

- **Medio de pago electrónico.** Solo el 19,7 % de las facturas a personas naturales sirve para la deducción del 1 %, porque el resto no informa pago electrónico ([cifras-dian.md](cifras-dian.md)). Un informe "compras deducibles al 1 %" necesitaría el **medio** de pago (`cac:PaymentMeans/cbc:PaymentMeansCode`), que desde el 2026-11-20 el parser guarda (esquema versión 3, tabla 13.3.4.2 cotejada). Qué códigos cuentan como pago electrónico es una regla tributaria: va en las reglas versionadas de `pro` (fase 6) y alimenta el borrador de renta (fase 7).
- **Competencia directa en MCP.** Alegra ya ofrece un MCP de solo lectura. La diferencia que hay que sostener y comunicar: independiente del software contable, desde el XML recibido, local.

## Fuentes

1. Consultor Contable, "Descargador XML FE" (página de venta). https://www.consultorcontable.com/descargador-xml-fe/ y https://www.consultorcontable.com/consultar-y-descargar-facturas-electronicas-recibidas/
2. La Nota Económica (contenido promocional de Siigo), "Deje de perseguir facturas: cinco tareas del contador que cambian con causación automática DIAN de Siigo Nube", 5-nov-2026. https://lanotaeconomica.com.co/movidas-empresarial/deje-de-perseguir-facturas-cinco-tareas-del-contador-que-cambian-con-causacion-automatica-dian-de-siigo-nube/
3. Siempre al Día (patrocinado por Alegra), "Facturas y documento equivalente con IA: ¿cómo revisarlos sin Excel?", actualizado el 18-jun-2026. https://siemprealdia.co/colombia/contabilidad/revisar-facturas-con-ia-y-documento-equivalente/
4. Accounter, "Verificador masivo de RUT y lector de eventos de facturas electrónicas". https://accounter.co/servicios/herramientas/verificador-masivo-de-rut-y-lector-de-eventos-de-facturas-electronicas-aplicativos-automatizados-dian
5. Portafolio, "Declaración de renta 2025: requisitos para obtener descuento para este año". https://www.portafolio.co/economia/impuestos/declaracion-de-renta-2025-requisitos-para-obtener-descuento-para-este-ano-624426 ; Siempre al Día, "Consulta de facturas electrónicas personas naturales". https://siemprealdia.co/colombia/impuestos/consulta-de-facturas-electronicas-personas-naturales/
