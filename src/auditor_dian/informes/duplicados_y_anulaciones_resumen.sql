SELECT hallazgo, moneda, count(*) AS documentos, sum(total) AS total, sum(valor_notas) AS valor_notas
FROM detalle
GROUP BY ALL
ORDER BY hallazgo, moneda
