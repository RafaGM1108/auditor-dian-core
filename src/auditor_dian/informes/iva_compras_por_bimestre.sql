-- Detalle: un documento y tarifa por fila. Solo el tributo 01 (IVA): un impuesto por unidad,
-- como el 22 de bolsas, trae una cantidad como base (decisión 0006, regla 6). Se suma por
-- tarifa porque hay emisores que repiten el mismo IVA en varios TaxSubtotal.
SELECT
    d.fecha_emision,
    printf('%d-%02d/%02d', year(d.fecha_emision),
           2 * ((month(d.fecha_emision) + 1) // 2) - 1,
           2 * ((month(d.fecha_emision) + 1) // 2)) AS bimestre,
    d.tipo,
    d.numero,
    d.cufe,
    d.emisor_identificacion,
    d.emisor_nombre,
    d.moneda,
    i.tarifa,
    sum(d.signo * i.base) AS base,
    sum(d.signo * i.valor) AS iva
FROM docs d
JOIN impuestos i USING (cufe)
WHERE i.codigo = '01'
GROUP BY ALL
ORDER BY bimestre, d.fecha_emision, d.numero, i.tarifa
