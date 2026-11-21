-- Forma de pago 2 = Crédito (Anexo DS 1.1, tabla 16.3.4.1; la del Anexo FE 1.9 está en la
-- Caja de Herramientas). El vencimiento no decide: hay emisores que lo ponen en ventas de
-- contado (SPEC §7). Core no consulta la DIAN: los eventos quedan "por verificar".
SELECT
    fecha_emision,
    fecha_vencimiento,
    fecha_vencimiento - fecha_emision AS dias_plazo,
    forma_pago,
    tipo,
    numero,
    cufe,
    emisor_identificacion,
    emisor_nombre,
    moneda,
    signo * total_pagar AS total,
    'por verificar' AS eventos
FROM docs
WHERE forma_pago = '2'
ORDER BY emisor_identificacion, fecha_emision, numero
