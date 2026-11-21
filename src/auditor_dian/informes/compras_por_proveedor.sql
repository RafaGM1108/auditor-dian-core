-- Detalle: un documento por fila, con los montos ya firmados (decisión 0006).
SELECT
    fecha_emision,
    tipo,
    numero,
    cufe,
    emisor_identificacion,
    emisor_nombre,
    moneda,
    signo * subtotal AS subtotal,
    signo * total_pagar AS total
FROM docs
ORDER BY emisor_identificacion, fecha_emision, numero
