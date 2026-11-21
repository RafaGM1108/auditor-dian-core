# Graph Report - auditor-dian-core  (2026-11-20)

## Corpus Check
- 78 files · ~45,356 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 14 file(s) not represented in the graph (top: .xml 7, (none) 4, .tex 1)

## Summary
- 778 nodes · 1626 edges · 56 communities (33 shown, 23 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 167 edges (avg confidence: 0.89)
- Token cost: 100,012 input · 0 output

## Graph Freshness
- Built from commit: `0dfd30a2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- herramienta
- ubl.py
- Ingesta y contenedor
- Hito M2 — Base y CLI
- Manifiesto de la extensión
- Decisión 0004: escala numérica
- Informes, Excel y sus pruebas
- servidor.py
- test_cli.py
- SPEC v0.1
- Decisión 0005 — Esquema de la base por cliente e identificación del cliente
- CI GitHub Actions
- cotejar_pdf.py
- attributes
- Decisión 0004: escala numérica
- test_servidor.py
- cli.py
- Resumen de hitos
- Investigación fase 0
- Proyecto raíz
- Decisión 0009: licencia MIT y nombre
- Anexo Técnico: versión vigente y rutas usadas
- body
- Decisión 0001: estructura con uv y src/
- 0011 — La información de un cliente nunca termina en otro
- 0010 — Carga de facturas desde Claude
- Cronograma y plan de documentación — Auditor DIAN
- test_plugins.py
- Investigación: cifras, normas y herramientas
- Empaquetado .mcpb
- 0012 — Publicación en un repositorio nuevo, con el historial aparte
- exportar_informe
- CLAUDE.md — auditor-dian-core
- plugins.py
- ingerir_facturas
- Resumen
- _origen

## God Nodes (most connected - your core abstractions)
1. `fixture()` - 51 edges
2. `abrir()` - 25 edges
3. `ejecutar()` - 25 edges
4. `error()` - 24 edges
5. `ingerir()` - 23 edges
6. `llamar()` - 22 edges
7. `leer_xml()` - 21 edges
8. `crear_cliente()` - 20 edges
9. `contenedor()` - 20 edges
10. `informe()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Advertencia valor_redondeado (nunca redondear en silencio)` --implements--> `_ajustar()`  [INFERRED]
  docs/decisiones/0004-escala-numerica.md → src/auditor_dian/ingesta.py
- `Hallazgos con facturas reales` --references--> `facturas_credito()`  [INFERRED]
  docs/hitos/M3.md → src/auditor_dian/servidor.py
- `Decisión` --references--> `App`  [INFERRED]
  docs/decisiones/0008-interfaz-de-plugins.md → src/auditor_dian/plugins.py
- `Resumen` --references--> `App`  [INFERRED]
  docs/hitos/M5.md → src/auditor_dian/plugins.py
- `Esquema versión 1 y tabla schema_version` --references--> `abrir()`  [EXTRACTED]
  docs/decisiones/0005-esquema-de-la-base.md → src/auditor_dian/base.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Exactitud numérica: guardar exacto y redondear solo al presentar** — docs_decisiones_0004_escala_numerica_decision, claude_montos_decimal, spec_escala_numerica, docs_decisiones_0004_escala_numerica_valor_redondeado, docs_bitacora_redondeo_silencioso_duckdb [INFERRED 0.85]
- **Idempotencia de la ingesta (SHA-256 + CUFE)** — spec_idempotencia, docs_decisiones_0005_esquema_de_la_base_idempotencia_dos_niveles, docs_bitacora_sha256_archivo_recibido, docs_hitos_m2_test_reingerir_no_duplica_nada, src_auditor_dian_ingesta_ingerir [INFERRED 0.85]
- **Salvedad de facturas reales arrastrada de M1 a M3** — docs_hitos_m1_salvedad_fixtures_sinteticos, docs_hitos_m2_salvedad, docs_bitacora_cierre_m2, spec_criterios_aceptacion, docs_cronograma_fase_0_investigacion [INFERRED 0.85]

## Communities (56 total, 23 thin omitted)

### Community 0 - "herramienta"
Cohesion: 0.22
Nodes (6): leer_sql(), duplicados_y_anulaciones(), facturas_credito(), herramienta(), historial_cliente(), resumen_periodo()

### Community 1 - "ubl.py"
Cohesion: 0.05
Nodes (55): Dataclasses inmutables de modelos.py, Sesión M1 pasos 1 y 2: factura y notas (ubl.py), Protección XXE, _advertir(), _parsear(), _advertencias(), _ajustar(), _existe() (+47 more)

### Community 2 - "Ingesta y contenedor"
Cohesion: 0.10
Nodes (46): leer_xml(), ingerir(), ingerir_lecturas(), Resumen, Separacion, separar(), leer_ruta(), crear_cliente() (+38 more)

### Community 3 - "Hito M2 — Base y CLI"
Cohesion: 0.11
Nodes (20): Advertencia campo_faltante: trm, Sesión: cierre de M1 (con salvedad), Sesión M1 paso 5: exportación, contingencia, documento soporte y nota de ajuste, Pendiente: montos en moneda extranjera, Fase 0: investigación y preparación, Fases 1–5 de core (M1 a M5), 0003 — pytest-cov para medir cobertura, Hito M1 — Parser (+12 more)

### Community 4 - "Manifiesto de la extensión"
Cohesion: 0.06
Nodes (35): author, name, default, description, required, title, type, compatibility (+27 more)

### Community 5 - "Decisión 0004: escala numérica"
Cohesion: 0.14
Nodes (11): AUDITOR_DIAN_HOME temporal en pruebas, Sesión M2 paso 1: esquema y base por cliente, DuckDB redondea en silencio y no acepta offset negativo, Alternativas descartadas: DECIMAL(18,2), DECIMAL(18,6), texto, DECIMAL(21,6) para montos, precios, cantidades y TRM, DECIMAL(9,3) para tarifas, Hora de emisión en TIMETZ vía CAST(? AS TIMETZ), Anexo Técnico FE versión 1.9 (+3 more)

### Community 6 - "Informes, Excel y sus pruebas"
Cohesion: 0.08
Nodes (24): exportar(), _tabla(), consultar(), disponibles(), ejecutar(), InformeDesconocido, registrar(), Resultado (+16 more)

### Community 7 - "servidor.py"
Cohesion: 0.15
Nodes (5): _fila(), _historial(), _icono(), _json(), _normalizar()

### Community 8 - "test_cli.py"
Cohesion: 0.42
Nodes (8): auditor(), test_archivo_que_no_se_pudo_guardar_termina_con_error(), test_ayuda_responde(), test_crear_cliente(), test_crear_cliente_invalido_explica_el_formato(), test_ingerir_cliente_inexistente(), test_ingerir_ruta_inexistente(), test_ingerir_y_reingerir()

### Community 9 - "SPEC v0.1"
Cohesion: 0.16
Nodes (8): README de auditor-dian-core, auditor-dian-core: librería + CLI + servidor MCP, Calidad y pruebas: fixtures sintéticos y CI, SPEC — auditor-dian-core v0.1, Fuera de alcance v0.1, Pendientes: licencia MIT vs AGPL-3.0 y nombre público, Extensiones por plugins (entry points auditor_dian.plugins), Servidor MCP stdio de solo lectura

### Community 10 - "Decisión 0005 — Esquema de la base por cliente e identificación del cliente"
Cohesion: 0.13
Nodes (10): Advertencias de ingesta (adquirente_distinto, documento_sin_cufe, error_lectura, valor_redondeado, cufe_repetido), Sesión M2 paso 2: ingesta idempotente, NaN e Infinity como valor_invalido, Consecuencia: cambiar el esquema exige subir VERSION_ESQUEMA y migración, Tabla única advertencias, Pendiente: referencias de notas (resuelto en 0005), Criterio de cierre: test_reingerir_no_duplica_nada, Advertencia adquirente_distinto (+2 more)

### Community 11 - "CI GitHub Actions"
Cohesion: 0.12
Nodes (15): jobs, pruebas, python, name, on, pull_request, push, runs-on (+7 more)

### Community 12 - "cotejar_pdf.py"
Cohesion: 0.31
Nodes (4): cotejar(), main(), _texto_pdf(), valores()

### Community 15 - "attributes"
Cohesion: 0.13
Nodes (14): description, label, placeholder, render, value, body, attributes, id (+6 more)

### Community 16 - "Decisión 0004: escala numérica"
Cohesion: 0.33
Nodes (5): 0004 — Escala numérica en la base: guardar exacto lo que trae el XML, Alternativas descartadas, Consecuencias, Contexto, Decisión

### Community 17 - "test_servidor.py"
Cohesion: 0.12
Nodes (30): casa(), error(), llamar(), test_auditor_mcp_responde_por_stdio(), test_buscar_cliente_e_historial(), test_buscar_documentos_limita_las_filas_y_cuenta_todas(), test_buscar_documentos_por_emisor_tipo_y_valor(), test_buscar_sin_coincidencias() (+22 more)

### Community 18 - "cli.py"
Cohesion: 0.08
Nodes (29): command, abrir(), crear_cliente(), digito_verificacion(), ErrorCliente, inicio(), normalizar_id(), ruta_base() (+21 more)

### Community 22 - "Decisión 0009: licencia MIT y nombre"
Cohesion: 0.33
Nodes (5): 0009 — Licencia MIT y nombre público, Alternativas descartadas, Consecuencias, Contexto, Decisión

### Community 27 - "Anexo Técnico: versión vigente y rutas usadas"
Cohesion: 0.05
Nodes (41): Sesión M1 paso 3: AttachedDocument (leer_xml), Sesión: cotejo contra el Anexo Técnico, Quitar declaración encoding del documento embebido, tests/fabrica.py: contenedores sintéticos, Advertencia validacion_de_otro_documento, 0006 — Reglas comunes de los informes, Alternativas descartadas, Consecuencias (+33 more)

### Community 32 - "body"
Cohesion: 0.14
Nodes (13): description, label, render, value, body, attributes, id, type (+5 more)

### Community 33 - "Decisión 0001: estructura con uv y src/"
Cohesion: 0.18
Nodes (7): Códigos de salida de ingerir (0, 1, 2), Sesión M2 paso 3: comandos clientes crear e ingerir, Decisión 0001: estructura con uv y src/, 0003 — pytest-cov para medir cobertura, pytest-cov, CLI auditor (clientes crear, ingerir, informe, mcp), Stack: Python 3.11, uv, lxml, duckdb, openpyxl, mcp, typer, pytest

### Community 34 - "0011 — La información de un cliente nunca termina en otro"
Cohesion: 0.17
Nodes (10): 0011 — La información de un cliente nunca termina en otro, Alternativas descartadas, Consecuencias, Contexto, Decisión, Cómo reportar una vulnerabilidad, Modelo de seguridad, Política de seguridad (+2 more)

### Community 36 - "0010 — Carga de facturas desde Claude"
Cohesion: 0.40
Nodes (4): 0010 — Carga de facturas desde Claude, Alternativas descartadas, Consecuencias, Contexto

### Community 37 - "Cronograma y plan de documentación — Auditor DIAN"
Cohesion: 0.13
Nodes (13): Sesión: cierre de M2, Decisión 0001 — Estructura del proyecto, Bitácora de desarrollo, Sesión: estructura inicial del proyecto, Sesión M1 paso 4: lector de ZIP, XML y carpetas, Cronograma y plan de documentación — Auditor DIAN, Fases pro P1–P4: reglas, lectores, cruces y borrador de renta, Estructura del informe final (docs/informe-final.md) (+5 more)

### Community 40 - "test_plugins.py"
Cohesion: 0.06
Nodes (28): 0008 — Interfaz de plugins, Alternativas descartadas, Consecuencias, Contexto, Decisión, Hallazgo, M5 — Plugins, Métricas (+20 more)

### Community 41 - "Investigación: cifras, normas y herramientas"
Cohesion: 0.10
Nodes (18): Calidad de las facturas que reciben las personas naturales, Cifras de facturación electrónica en Colombia, Contadores, Facturadores, Fuentes, RADIAN (facturas como título valor), Volumen, Fuentes (+10 more)

### Community 47 - "0012 — Publicación en un repositorio nuevo, con el historial aparte"
Cohesion: 0.33
Nodes (5): 0012 — Publicación en un repositorio nuevo, con el historial aparte, Alternativas descartadas, Consecuencias, Contexto, Decisión

### Community 48 - "exportar_informe"
Cohesion: 0.23
Nodes (11): 0007 — Servidor MCP, Alternativas descartadas, Consecuencias, Contexto, Decisión, abrir_cliente(), buscar_documentos(), _ejecutar() (+3 more)

### Community 49 - "CLAUDE.md — auditor-dian-core"
Cohesion: 0.14
Nodes (11): Commits en español e imperativo, CLAUDE.md — auditor-dian-core, Mapa del código: grafo de conocimiento graphify-out, Sesión: grafo de conocimiento del repositorio, 0002 — Grafo de conocimiento del repositorio versionado, Alternativas descartadas, Consecuencias, Contexto (+3 more)

### Community 50 - "plugins.py"
Cohesion: 0.17
Nodes (4): descripcion(), registrar(), nombres_invalidos(), test_nombres_de_herramientas_y_parametros_validos_para_la_api_de_claude()

### Community 51 - "ingerir_facturas"
Cohesion: 0.21
Nodes (8): Decisión, _abrir_para_cargar(), _descargas(), diagnostico(), ingerir_facturas(), ingerir_por_cliente(), listar_clientes(), _resumen()

### Community 54 - "Resumen"
Cohesion: 0.29
Nodes (5): Criterio de cierre, M4 — Servidor MCP, Métricas, Pendientes que pasan a M5, Resumen

### Community 55 - "_origen"
Cohesion: 0.47
Nodes (3): _candidatas(), _origen(), _sin_mayusculas()

## Knowledge Gaps
- **36 isolated node(s):** `auditor-dian-core`, `Advertencia campo_faltante: trm`, `Exportación a .xlsx (resumen + detalle)`, `Impuestos (cac:TaxTotal)`, `Informe facturas_credito` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 281 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Anexo Técnico: versión vigente y rutas usadas` connect `Anexo Técnico: versión vigente y rutas usadas` to `ubl.py`, `Hito M2 — Base y CLI`, `Decisión 0004: escala numérica`, `test_plugins.py`, `Investigación: cifras, normas y herramientas`, `Resumen`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `abrir()` (e.g. with `crear_base_comun()` and `test_abrir_base_de_otra_version()`) actually correct?**
  _`abrir()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auditor-dian-core`, `Advertencia campo_faltante: trm`, `Exportación a .xlsx (resumen + detalle)` to the rest of the system?**
  _36 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ubl.py` be split into smaller, more focused modules?**
  _Cohesion score 0.051511758118701005 - nodes in this community are weakly interconnected._
- **Why does `CLI auditor (clientes crear, ingerir, informe, mcp)` connect `Decisión 0001: estructura con uv y src/` to `SPEC v0.1`, `cli.py`, `Hito M2 — Base y CLI`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `ejecutar()` (e.g. with `test_compras_por_proveedor_resta_notas_credito_y_de_ajuste()` and `test_duplicados_y_anulaciones()`) actually correct?**
  _`ejecutar()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `Ingesta y contenedor` be split into smaller, more focused modules?**
  _Cohesion score 0.10168350168350168 - nodes in this community are weakly interconnected._