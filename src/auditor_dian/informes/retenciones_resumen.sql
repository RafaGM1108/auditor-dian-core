SELECT
    mes,
    moneda,
    codigo,
    tributo,
    count(DISTINCT cufe) AS documentos,
    sum(base) AS base,
    sum(valor) AS valor
FROM detalle
GROUP BY ALL
ORDER BY mes, moneda, codigo
