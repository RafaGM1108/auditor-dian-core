-- Sin respuesta DIAN en el contenedor (validado_dian NULL) o rechazadas (código 04, AAH03),
-- con el archivo de donde salieron para ubicarlas (decisión 0006, regla 5).
SELECT
    CASE WHEN d.validado_dian IS NULL THEN 'sin_respuesta' ELSE 'rechazada' END AS estado,
    d.fecha_emision,
    d.tipo,
    d.numero,
    d.cufe,
    d.emisor_identificacion,
    d.emisor_nombre,
    d.moneda,
    d.signo * d.total_pagar AS total,
    a.ruta AS archivo,
    d.miembro
FROM docs d
JOIN archivos_ingeridos a USING (sha256)
WHERE d.validado_dian IS NOT TRUE
ORDER BY estado, d.fecha_emision, d.numero
