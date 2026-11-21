SELECT
    bimestre,
    moneda,
    tarifa,
    count(DISTINCT cufe) AS documentos,
    sum(base) AS base,
    sum(iva) AS iva
FROM detalle
GROUP BY ALL
ORDER BY bimestre, moneda, tarifa
