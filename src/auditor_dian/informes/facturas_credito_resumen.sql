SELECT emisor_identificacion, max(emisor_nombre) AS emisor_nombre, moneda,
       count(*) AS documentos, sum(total) AS total
FROM detalle
GROUP BY emisor_identificacion, moneda
ORDER BY total DESC, emisor_identificacion
