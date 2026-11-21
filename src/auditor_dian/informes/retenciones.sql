-- Detalle: una retención por fila. En facturas y documento soporte son autorretenciones
-- declaradas por el emisor (Anexo FE 1.9 FAT01, Anexo DS 1.1 DSAT01). Nombres de la tabla
-- 13.2.2 Tributos de la Caja de Herramientas FE 1.9; un código fuera de ella queda sin nombre.
SELECT
    d.fecha_emision,
    strftime(d.fecha_emision, '%Y-%m') AS mes,
    d.tipo,
    d.numero,
    d.cufe,
    d.emisor_identificacion,
    d.emisor_nombre,
    d.moneda,
    r.codigo,
    t.nombre AS tributo,
    r.tarifa,
    d.signo * r.base AS base,
    d.signo * r.valor AS valor
FROM docs d
JOIN retenciones r USING (cufe)
LEFT JOIN (VALUES ('05', 'ReteIVA'), ('06', 'ReteRenta'), ('07', 'ReteICA')) t(codigo, nombre)
    ON t.codigo = r.codigo
ORDER BY mes, d.fecha_emision, d.numero, r.orden
