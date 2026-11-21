# 0011 — La información de un cliente nunca termina en otro

Fecha: 2026-11-20

## Contexto

El contador trabaja con muchos clientes en el mismo equipo. Si por error carga en un cliente las facturas o certificados de otra persona y esas cifras llegan a su declaración, el error es grave: impuesto mal liquidado, sanciones y responsabilidad del contador. Hasta ahora una factura de la que el cliente no era parte se guardaba con la advertencia `adquirente_distinto`. No contaba en los informes, pero quedaba en su base. En pro, los certificados de otra persona sí se rechazaban, pero se comparaban con el NIT tal como se escribió, que ahora puede traer puntos o dígito de verificación (decisión 0010).

## Decisión

Varios filtros independientes, de modo que si uno falla, el siguiente lo atrapa. La llave es la identificación que trae **dentro** cada documento: el NIT o la cédula del comprador, del vendedor o del titular.

1. **Al cargar facturas (core).** Un documento entra solo si el cliente es su comprador o su vendedor. Si no, no se guarda: queda la advertencia `documento_ajeno` y la respuesta lo dice (`rechazados_de_otra_persona`). Las facturas a consumidor final (`222222222222`, Anexo Técnico FE 1.9, campos FAK21 y CAK62) no se asignan a ningún cliente al repartir.
2. **Al cargar documentos de renta (pro).** La exógena, los certificados 220 y bancarios y la declaración anterior entran solo si su titular es el cliente registrado en la base. Se compara con la identificación guardada en la base, no con lo que se escribió.
3. **Al abrir la base.** La identificación guardada dentro de la base debe coincidir con la carpeta del cliente. Una base copiada o renombrada en la carpeta de otro cliente no se usa.
4. **Al consultar facturas (core).** Los informes solo cuentan documentos donde el cliente es el comprador. El historial y el diagnóstico cuentan los documentos ajenos que hayan quedado de versiones anteriores.
5. **Al consultar renta (pro).** Antes de dar cualquier cifra se verifica que todo lo guardado sea del cliente. Si hay algo ajeno, no se da ninguna cifra y se dice qué documento es.
6. **Al repartir por cliente.** La identificación del XML se compara exacta: no se interpreta como la que escribe el usuario (`EXT-000123` no es el cliente `000123`).

## Alternativas descartadas

- **Sellar o transformar los datos con un hash por cliente**, que fue la idea inicial. Cada archivo ya se guarda con su SHA-256, lo que permite rastrearlo y evita cargarlo dos veces. Pero un hash no dice de quién es un documento: dos personas pueden cargar el mismo archivo y producir el mismo hash. Lo que identifica al dueño es el NIT o la cédula que trae el propio documento, firmado por el emisor. Por eso los filtros usan esa identificación. Cifrar las bases por cliente protegería contra otro riesgo, el acceso de terceros al equipo, y queda para cuando haya multiusuario (plan Team).
- **Guardar con advertencia** (lo de antes): deja la decisión en manos de quien lea la advertencia, y un usuario no técnico no la lee.
- **Comparar también el nombre**: los nombres cambian entre documentos ("S.A.S.", abreviaturas), así que daría falsas alarmas. Queda como posible aviso suave, no como filtro.

## Consecuencias

- Las facturas que emite el cliente (ventas) se siguen guardando, con la advertencia `adquirente_distinto`, porque pro las usa como soporte de lo que reporta la exógena.
- Una base cargada con versiones anteriores puede traer documentos ajenos. Core los excluye y los cuenta. Pro se niega a dar cifras hasta que se cree el cliente de nuevo.
- El conteo de documentos de la base de pruebas común bajó de 8 a 7: la factura de exportación de ejemplo no es del cliente.
