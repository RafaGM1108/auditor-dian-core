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
SELECT CASE WHEN a.sin_repartir THEN 'anulada_sin_repartir'
            WHEN abs(d.total_pagar - a.valor_notas) <= 2 THEN 'anulada_total'
            ELSE 'anulada_parcial' END,
       d.fecha_emision, d.tipo, d.numero, d.cufe, d.emisor_identificacion, d.emisor_nombre,
       d.moneda, d.total_pagar, a.valor_notas, a.notas
FROM docs d
JOIN (
    SELECT cufe, sum(parte) AS valor_notas, bool_or(parte IS NULL) AS sin_repartir,
           string_agg(nota, ', ' ORDER BY nota) AS notas
    FROM (
        -- Lo que cada nota descuenta de cada factura que cita (decisión 0013): todo su total
        -- si cita una sola; si cita varias, cada factura su propio total cuando la nota suma lo
        -- mismo que todas (±2,00) y están todas cargadas; si no, el reparto no se sabe (NULL).
        SELECT cufe, nota,
               CASE WHEN citadas = 1 THEN total_nota
                    WHEN count(*) OVER nota = citadas
                         AND abs(total_nota - sum(total_factura) OVER nota) <= 2
                    THEN total_factura
               END AS parte
        FROM (
            SELECT n.cufe AS nota_cufe, n.numero AS nota, n.total_pagar AS total_nota,
                   f.cufe, f.total_pagar AS total_factura,
                   (SELECT count(*) FROM referencias c WHERE c.cufe = n.cufe) AS citadas
            FROM documentos n
            JOIN referencias r ON r.cufe = n.cufe
            -- Facturas: 01, 02, 03 y 04 (Caja de Herramientas FE 1.9, tabla 13.1.3), de
            -- cualquier fecha: una nota de marzo puede citar facturas de febrero y de marzo.
            JOIN documentos f
              ON f.tipo IN ('01', '02', '03', '04')
             AND f.adquirente_identificacion = n.adquirente_identificacion
             AND (r.cufe_referenciado = f.cufe
                  OR (r.cufe_referenciado IS NULL AND r.numero = f.numero
                      AND n.emisor_identificacion = f.emisor_identificacion))
            WHERE n.tipo = '91' AND n.adquirente_identificacion = (SELECT id FROM cliente)
        )
        WINDOW nota AS (PARTITION BY nota_cufe)
    )
    GROUP BY cufe
) a USING (cufe)
ORDER BY hallazgo, emisor_identificacion, numero, fecha_emision
