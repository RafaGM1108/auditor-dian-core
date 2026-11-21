SELECT estado, moneda, count(*) AS documentos, sum(total) AS total
FROM detalle
GROUP BY ALL
ORDER BY estado, moneda
