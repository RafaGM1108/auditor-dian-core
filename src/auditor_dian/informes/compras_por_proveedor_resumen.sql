-- Un proveedor por fila y moneda. El nombre puede variar entre documentos del mismo NIT
-- ("ÉXITO" / "EXITO"), así que se agrupa solo por NIT y se muestra uno de los nombres.
SELECT
    emisor_identificacion,
    max(emisor_nombre) AS emisor_nombre,
    moneda,
    count(*) AS documentos,
    sum(subtotal) AS subtotal,
    sum(total) AS total
FROM detalle
GROUP BY emisor_identificacion, moneda
ORDER BY total DESC, emisor_identificacion
