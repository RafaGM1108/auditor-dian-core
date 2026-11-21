-- Dos hallazgos con las mismas columnas (decisión 0006, regla 4):
-- 1. duplicado: mismo emisor y número con distinto CUFE, entre los documentos del rango.
-- 2. anulada_total / anulada_parcial: factura del rango citada por notas crédito del cliente
--    de cualquier fecha (una nota de marzo puede anular una factura de febrero). La anulación
--    es total si las notas suman el total de la factura con ±2,00 (Anexo FE 1.9, 5.2.1.1).
-- Sin WITH propio: el informe ya corre dentro del WITH que define `docs`.
SELECT 'duplicado' AS hallazgo, fecha_emision, tipo, numero, cufe, emisor_identificacion,
       emisor_nombre, moneda, total_pagar AS total, NULL::DECIMAL(21, 6) AS valor_notas,
       repetidos || ' documentos con este número' AS relacionados
FROM (
    SELECT *, count(*) OVER (PARTITION BY emisor_identificacion, numero) AS repetidos
    FROM docs
)
WHERE repetidos > 1
UNION ALL
SELECT CASE WHEN abs(d.total_pagar - a.valor_notas) <= 2 THEN 'anulada_total'
            ELSE 'anulada_parcial' END,
       d.fecha_emision, d.tipo, d.numero, d.cufe, d.emisor_identificacion, d.emisor_nombre,
       d.moneda, d.total_pagar, a.valor_notas, a.notas
FROM docs d
JOIN (
    -- shortcut: una nota que cita varias facturas descuenta su total completo de cada una;
    -- revisar si aparece un caso real.
    SELECT f.cufe, sum(n.total_pagar) AS valor_notas,
           string_agg(n.nota, ', ' ORDER BY n.nota) AS notas
    FROM docs f
    JOIN (
        SELECT n.numero AS nota, n.total_pagar, n.emisor_identificacion, r.cufe_referenciado,
               r.numero
        FROM documentos n
        JOIN referencias r USING (cufe)
        WHERE n.tipo = '91' AND n.adquirente_identificacion = (SELECT id FROM cliente)
    ) n ON n.cufe_referenciado = f.cufe
        OR (n.cufe_referenciado IS NULL AND n.numero = f.numero
            AND n.emisor_identificacion = f.emisor_identificacion)
    -- Facturas: 01, 02, 03 y 04 (Caja de Herramientas FE 1.9, tabla 13.1.3).
    WHERE f.tipo IN ('01', '02', '03', '04')
    GROUP BY f.cufe
) a USING (cufe)
ORDER BY hallazgo, emisor_identificacion, numero, fecha_emision
