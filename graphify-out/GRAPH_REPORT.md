# Graph Report - auditor-dian-core  (2026-11-20)

## Corpus Check
- 76 files · ~43,522 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 14 file(s) not represented in the graph (top: .xml 7, (none) 4, .tex 1)

## Summary
- 761 nodes · 1610 edges · 61 communities (38 shown, 23 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 167 edges (avg confidence: 0.89)
- Token cost: 100,012 input · 0 output

## Graph Freshness
- Built from commit: `6a301ef0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Anexo Técnico: versión vigente y rutas usadas
- test_ubl.py
- Ingesta y contenedor
- Anexo Técnico: versión vigente y rutas usadas
- Manifiesto de la extensión
- Decisión 0004: escala numérica
- Informes, Excel y sus pruebas
- servidor.py
- Resultado del cotejo de rutas del parser
- SPEC v0.1
- Decisión 0005 — Esquema de la base por cliente e identificación del cliente
- CI GitHub Actions
- ingesta.py
- Bitácora de desarrollo
- attributes
- Decisión 0004: escala numérica
- test_servidor.py
- cli.py
- Resumen de hitos
- Investigación fase 0
- Proyecto raíz
- Decisión 0009: licencia MIT y nombre
- M3 y reglas de los informes (0006)
- body
- Decisión 0001: estructura con uv y src/
- 0011 — La información de un cliente nunca termina en otro
- 0010 — Carga de facturas desde Claude
- cli.py
- test_plugins.py
- Investigación: cifras, normas y herramientas
- ubl.py
- Empaquetado .mcpb
- _Lectura
- exportar_informe
- herramienta
- cotejar_pdf.py
- ingerir_facturas
- test_cli.py
- Parte
- Resumen
- _origen
- _json

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
- `Hallazgos con facturas reales` --references--> `facturas_credito()`  [INFERRED]
  docs/hitos/M3.md → src/auditor_dian/servidor.py
- `Advertencia valor_redondeado (nunca redondear en silencio)` --implements--> `_ajustar()`  [INFERRED]
  docs/decisiones/0004-escala-numerica.md → src/auditor_dian/ingesta.py
- `Resumen` --references--> `listar_clientes()`  [INFERRED]
  docs/hitos/M4.md → src/auditor_dian/servidor.py
- `Decisión` --references--> `historial_cliente()`  [INFERRED]
  docs/decisiones/0010-carga-desde-claude.md → src/auditor_dian/servidor.py
- `Alternativas descartadas` --references--> `buscar_documentos()`  [INFERRED]
  docs/decisiones/0007-servidor-mcp.md → src/auditor_dian/servidor.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Exactitud numérica: guardar exacto y redondear solo al presentar** — docs_decisiones_0004_escala_numerica_decision, claude_montos_decimal, spec_escala_numerica, docs_decisiones_0004_escala_numerica_valor_redondeado, docs_bitacora_redondeo_silencioso_duckdb [INFERRED 0.85]
- **Idempotencia de la ingesta (SHA-256 + CUFE)** — spec_idempotencia, docs_decisiones_0005_esquema_de_la_base_idempotencia_dos_niveles, docs_bitacora_sha256_archivo_recibido, docs_hitos_m2_test_reingerir_no_duplica_nada, src_auditor_dian_ingesta_ingerir [INFERRED 0.85]
- **Salvedad de facturas reales arrastrada de M1 a M3** — docs_hitos_m1_salvedad_fixtures_sinteticos, docs_hitos_m2_salvedad, docs_bitacora_cierre_m2, spec_criterios_aceptacion, docs_cronograma_fase_0_investigacion [INFERRED 0.85]

## Communities (61 total, 23 thin omitted)

### Community 0 - "Anexo Técnico: versión vigente y rutas usadas"
Cohesion: 0.20
Nodes (10): Campos a extraer (documento, impuestos, retenciones, líneas, ingesta), CUFE/CUDE (cbc:UUID), Exportación a .xlsx (resumen + detalle), Impuestos (cac:TaxTotal), Informe duplicados_y_anulaciones, Informe facturas_credito, Informe iva_compras_por_bimestre, Informe retenciones (autorretenciones del emisor) (+2 more)

### Community 1 - "test_ubl.py"
Cohesion: 0.15
Nodes (22): Tributo, leer_documento(), test_cli_informe_errores(), test_detecta_nombres_que_la_api_rechaza(), leer(), test_campo_obligatorio_faltante_queda_en_none_con_advertencia(), test_documento_soporte_compra_a_persona_natural(), test_factura_con_cargo_global_lee_todos_los_totales() (+14 more)

### Community 2 - "Ingesta y contenedor"
Cohesion: 0.11
Nodes (43): leer_xml(), ingerir(), Separacion, separar(), leer_ruta(), crear_cliente(), contenedor(), fixture() (+35 more)

### Community 3 - "Anexo Técnico: versión vigente y rutas usadas"
Cohesion: 0.14
Nodes (18): Advertencia campo_faltante: trm, Sesión: cotejo contra el Anexo Técnico, Sesión M1 paso 5: exportación, contingencia, documento soporte y nota de ajuste, Pendiente: montos en moneda extranjera, Fase 0: investigación y preparación, Pendiente: moneda extranjera en informes de M3, Hito M2 — Base y CLI, Métricas de M2 (59 pruebas, 100 % de 407 sentencias, 0 reales) (+10 more)

### Community 4 - "Manifiesto de la extensión"
Cohesion: 0.06
Nodes (35): author, name, default, description, required, title, type, compatibility (+27 more)

### Community 5 - "Decisión 0004: escala numérica"
Cohesion: 0.20
Nodes (9): Sesión M2 paso 1: esquema y base por cliente, DuckDB redondea en silencio y no acepta offset negativo, Alternativas descartadas: DECIMAL(18,2), DECIMAL(18,6), texto, DECIMAL(21,6) para montos, precios, cantidades y TRM, DECIMAL(9,3) para tarifas, Hora de emisión en TIMETZ vía CAST(? AS TIMETZ), Anexo Técnico FE versión 1.9, Resolución 000008 de 2024 (adopción obligatoria de la 1.9) (+1 more)

### Community 6 - "Informes, Excel y sus pruebas"
Cohesion: 0.07
Nodes (27): AUDITOR_DIAN_HOME temporal en pruebas, exportar(), _tabla(), consultar(), disponibles(), ejecutar(), InformeDesconocido, registrar() (+19 more)

### Community 7 - "servidor.py"
Cohesion: 0.14
Nodes (4): descripcion(), registrar(), _icono(), _normalizar()

### Community 8 - "Resultado del cotejo de rutas del parser"
Cohesion: 0.12
Nodes (18): Sesión: cierre de M1 (con salvedad), Fases 1–5 de core (M1 a M5), 0003 — pytest-cov para medir cobertura, Hito M1 — Parser, Métricas de M1 (7 tipos, 31 pruebas, 100 % cobertura, 0 reales), Pendiente: precisión en la base (resuelto en 0004), Pendiente: ZIP dentro de ZIP, Anexo Técnico Documento Soporte versión 1.1 (+10 more)

### Community 9 - "SPEC v0.1"
Cohesion: 0.09
Nodes (16): Commits en español e imperativo, CLAUDE.md — auditor-dian-core, 0002 — Grafo de conocimiento del repositorio versionado, Alternativas descartadas, Consecuencias, Contexto, Decisión, graphify (grafo en graphify-out/) (+8 more)

### Community 10 - "Decisión 0005 — Esquema de la base por cliente e identificación del cliente"
Cohesion: 0.13
Nodes (10): Advertencias de ingesta (adquirente_distinto, documento_sin_cufe, error_lectura, valor_redondeado, cufe_repetido), Sesión M2 paso 2: ingesta idempotente, NaN e Infinity como valor_invalido, Consecuencia: cambiar el esquema exige subir VERSION_ESQUEMA y migración, Tabla única advertencias, Pendiente: referencias de notas (resuelto en 0005), Criterio de cierre: test_reingerir_no_duplica_nada, Advertencia adquirente_distinto (+2 more)

### Community 11 - "CI GitHub Actions"
Cohesion: 0.18
Nodes (10): jobs, pruebas, name, on, pull_request, push, runs-on, steps (+2 more)

### Community 12 - "ingesta.py"
Cohesion: 0.30
Nodes (11): _advertencias(), _ajustar(), _existe(), _guardar_archivo(), _guardar_documento(), monto(), ingerir_lecturas(), _insertar() (+3 more)

### Community 13 - "Bitácora de desarrollo"
Cohesion: 0.09
Nodes (20): Mapa del código: grafo de conocimiento graphify-out, Sesión: cierre de M2, Sesión M1 paso 3: AttachedDocument (leer_xml), Decisión 0001 — Estructura del proyecto, Bitácora de desarrollo, Quitar declaración encoding del documento embebido, Sesión: estructura inicial del proyecto, tests/fabrica.py: contenedores sintéticos (+12 more)

### Community 15 - "attributes"
Cohesion: 0.13
Nodes (14): description, label, placeholder, render, value, body, attributes, id (+6 more)

### Community 16 - "Decisión 0004: escala numérica"
Cohesion: 0.33
Nodes (5): 0004 — Escala numérica en la base: guardar exacto lo que trae el XML, Alternativas descartadas, Consecuencias, Contexto, Decisión

### Community 17 - "test_servidor.py"
Cohesion: 0.12
Nodes (31): anyio_backend(), casa(), error(), llamar(), test_auditor_mcp_responde_por_stdio(), test_buscar_cliente_e_historial(), test_buscar_documentos_limita_las_filas_y_cuenta_todas(), test_buscar_documentos_por_emisor_tipo_y_valor() (+23 more)

### Community 18 - "cli.py"
Cohesion: 0.14
Nodes (21): abrir(), crear_cliente(), digito_verificacion(), ErrorCliente, inicio(), normalizar_id(), ruta_base(), ruta_exacta() (+13 more)

### Community 22 - "Decisión 0009: licencia MIT y nombre"
Cohesion: 0.33
Nodes (5): 0009 — Licencia MIT y nombre público, Alternativas descartadas, Consecuencias, Contexto, Decisión

### Community 27 - "M3 y reglas de los informes (0006)"
Cohesion: 0.15
Nodes (11): 0006 — Reglas comunes de los informes, Alternativas descartadas, Consecuencias, Contexto, Decisión, Criterio de cierre, Hallazgos con facturas reales, M3 — Informes (+3 more)

### Community 32 - "body"
Cohesion: 0.14
Nodes (13): description, label, render, value, body, attributes, id, type (+5 more)

### Community 33 - "Decisión 0001: estructura con uv y src/"
Cohesion: 0.25
Nodes (4): Decisión 0001: estructura con uv y src/, 0003 — pytest-cov para medir cobertura, pytest-cov, Stack: Python 3.11, uv, lxml, duckdb, openpyxl, mcp, typer, pytest

### Community 34 - "0011 — La información de un cliente nunca termina en otro"
Cohesion: 0.33
Nodes (5): 0011 — La información de un cliente nunca termina en otro, Alternativas descartadas, Consecuencias, Contexto, Decisión

### Community 36 - "0010 — Carga de facturas desde Claude"
Cohesion: 0.40
Nodes (4): 0010 — Carga de facturas desde Claude, Alternativas descartadas, Consecuencias, Contexto

### Community 37 - "cli.py"
Cohesion: 0.10
Nodes (12): Códigos de salida de ingerir (0, 1, 2), Sesión M2 paso 3: comandos clientes crear e ingerir, command, CLI auditor (clientes crear, ingerir, informe, mcp), crear(), _fallar(), informe(), ingerir() (+4 more)

### Community 40 - "test_plugins.py"
Cohesion: 0.06
Nodes (29): 0008 — Interfaz de plugins, Alternativas descartadas, Consecuencias, Contexto, Decisión, Hallazgo, M5 — Plugins, Métricas (+21 more)

### Community 41 - "Investigación: cifras, normas y herramientas"
Cohesion: 0.10
Nodes (18): Calidad de las facturas que reciben las personas naturales, Cifras de facturación electrónica en Colombia, Contadores, Facturadores, Fuentes, RADIAN (facturas como título valor), Volumen, Fuentes (+10 more)

### Community 44 - "ubl.py"
Cohesion: 0.13
Nodes (14): Dataclasses inmutables de modelos.py, Sesión M1 pasos 1 y 2: factura y notas (ubl.py), Protección XXE, _advertir(), _parsear(), _leer(), leer_archivo(), Documento (+6 more)

### Community 47 - "_Lectura"
Cohesion: 0.27
Nodes (4): _decimal_finito(), _Lectura, _primero(), _texto()

### Community 48 - "exportar_informe"
Cohesion: 0.22
Nodes (11): 0007 — Servidor MCP, Alternativas descartadas, Consecuencias, Contexto, Decisión, abrir_cliente(), buscar_documentos(), _ejecutar() (+3 more)

### Community 49 - "herramienta"
Cohesion: 0.22
Nodes (6): leer_sql(), duplicados_y_anulaciones(), facturas_credito(), herramienta(), historial_cliente(), resumen_periodo()

### Community 50 - "cotejar_pdf.py"
Cohesion: 0.31
Nodes (4): cotejar(), main(), _texto_pdf(), valores()

### Community 51 - "ingerir_facturas"
Cohesion: 0.20
Nodes (7): Decisión, _abrir_para_cargar(), _clientes(), diagnostico(), ingerir_facturas(), listar_clientes(), _resumen()

### Community 52 - "test_cli.py"
Cohesion: 0.36
Nodes (8): auditor(), test_archivo_que_no_se_pudo_guardar_termina_con_error(), test_ayuda_responde(), test_crear_cliente(), test_crear_cliente_invalido_explica_el_formato(), test_ingerir_cliente_inexistente(), test_ingerir_ruta_inexistente(), test_ingerir_y_reingerir()

### Community 53 - "Parte"
Cohesion: 0.31
Nodes (5): Parte, leer_tiquete(), parte(), texto(), register()

### Community 54 - "Resumen"
Cohesion: 0.29
Nodes (5): Criterio de cierre, M4 — Servidor MCP, Métricas, Pendientes que pasan a M5, Resumen

### Community 55 - "_origen"
Cohesion: 0.38
Nodes (4): _candidatas(), _descargas(), _origen(), _sin_mayusculas()

### Community 56 - "_json"
Cohesion: 0.50
Nodes (3): _fila(), _historial(), _json()

## Knowledge Gaps
- **36 isolated node(s):** `auditor-dian-core`, `Advertencia campo_faltante: trm`, `Exportación a .xlsx (resumen + detalle)`, `Impuestos (cac:TaxTotal)`, `Informe facturas_credito` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 271 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Anexo Técnico: versión vigente y rutas usadas` connect `Anexo Técnico: versión vigente y rutas usadas` to `Anexo Técnico: versión vigente y rutas usadas`, `Decisión 0004: escala numérica`, `test_plugins.py`, `Resultado del cotejo de rutas del parser`, `Investigación: cifras, normas y herramientas`, `ubl.py`, `Resumen`, `M3 y reglas de los informes (0006)`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `abrir()` (e.g. with `crear_base_comun()` and `test_abrir_base_de_otra_version()`) actually correct?**
  _`abrir()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auditor-dian-core`, `Advertencia campo_faltante: trm`, `Exportación a .xlsx (resumen + detalle)` to the rest of the system?**
  _36 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Ingesta y contenedor` be split into smaller, more focused modules?**
  _Cohesion score 0.11010558069381599 - nodes in this community are weakly interconnected._
- **Why does `CLI auditor (clientes crear, ingerir, informe, mcp)` connect `cli.py` to `Decisión 0001: estructura con uv y src/`, `Anexo Técnico: versión vigente y rutas usadas`, `SPEC v0.1`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `ejecutar()` (e.g. with `test_compras_por_proveedor_resta_notas_credito_y_de_ajuste()` and `test_duplicados_y_anulaciones()`) actually correct?**
  _`ejecutar()` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Should `Anexo Técnico: versión vigente y rutas usadas` be split into smaller, more focused modules?**
  _Cohesion score 0.1368421052631579 - nodes in this community are weakly interconnected._