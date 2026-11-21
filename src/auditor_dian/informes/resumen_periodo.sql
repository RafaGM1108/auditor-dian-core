-- Para la herramienta MCP `resumen_periodo` (SPEC §10). Cada cifra sale ya sumada aquí, con
-- sus CUFE, para que el agente no tenga que calcular nada. Mismas reglas que los informes
-- (decisión 0006): notas crédito y de ajuste restan; IVA solo con el tributo 01.
SELECT 'compras_total' AS concepto, '' AS clave, moneda, count(*) AS documentos,
       sum(signo * total_pagar) AS valor, list(cufe ORDER BY cufe) AS cufes
FROM docs
GROUP BY moneda
UNION ALL
SELECT 'compras_por_tipo', tipo, moneda, count(*), sum(signo * total_pagar),
       list(cufe ORDER BY cufe)
FROM docs
GROUP BY tipo, moneda
UNION ALL
SELECT 'iva_total', '', d.moneda, count(DISTINCT d.cufe), sum(d.signo * i.valor),
       list(DISTINCT d.cufe ORDER BY d.cufe)
FROM docs d
JOIN impuestos i USING (cufe)
WHERE i.codigo = '01'
GROUP BY d.moneda
UNION ALL
SELECT 'iva_por_tarifa', i.tarifa::VARCHAR, d.moneda, count(DISTINCT d.cufe),
       sum(d.signo * i.valor), list(DISTINCT d.cufe ORDER BY d.cufe)
FROM docs d
JOIN impuestos i USING (cufe)
WHERE i.codigo = '01'
GROUP BY i.tarifa, d.moneda
UNION ALL
SELECT 'retenciones_por_codigo', r.codigo, d.moneda, count(DISTINCT d.cufe),
       sum(d.signo * r.valor), list(DISTINCT d.cufe ORDER BY d.cufe)
FROM docs d
JOIN retenciones r USING (cufe)
GROUP BY r.codigo, d.moneda
ORDER BY concepto, clave, moneda
