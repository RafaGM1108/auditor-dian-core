# Política de seguridad

Auditor DIAN maneja información tributaria de terceros: facturas, NIT, montos. Tomamos en serio cualquier falla que pueda exponerla, mezclarla entre clientes o alterarla.

## Versiones con soporte

| Versión | Soporte |
| --- | --- |
| Última publicada en [Releases](https://github.com/RafaGM1108/auditor-dian-core/releases/latest) | Sí |
| Anteriores | No: actualiza a la última |

## Cómo reportar una vulnerabilidad

**No abras un issue público.** Usa el reporte privado de GitHub: pestaña **Security → Report a vulnerability** de este repositorio. Incluye:

- la versión (la da *"dame el diagnóstico de Auditor DIAN"* en Claude);
- qué pasó y cómo reproducirlo, con archivos **sintéticos**: nunca facturas reales;
- el impacto que ves, por ejemplo si se exponen datos, se mezclan clientes o se alteran cifras.

Respondemos en un plazo de 7 días. Si confirmamos la falla, publicamos una versión corregida y te damos crédito en las notas, si quieres.

## Qué se considera una vulnerabilidad

- Que datos de un cliente terminen en la base o en las cifras de otro.
- Que se borre o modifique información ya cargada.
- Que un archivo (XML, ZIP) provoque lectura de archivos del equipo, llamadas de red, ejecución de código o un consumo desmedido de memoria o disco.
- Que una exportación sobrescriba un archivo existente.
- Que el diagnóstico para soporte exponga montos o contenido de facturas.

Una cifra que no coincide con la factura es un error, no una vulnerabilidad: repórtala con el formulario **Una cifra no cuadra**.

## Modelo de seguridad

- **Local.** El código no hace llamadas de red. Las bases y los archivos se quedan en el equipo del usuario.
- **Lector de XML endurecido.** Sin entidades externas ni acceso a la red (protección contra XXE). Cada XML se lee con un tope de tamaño real, no con el que declara el ZIP.
- **Solo agregar.** Las consultas abren la base en solo lectura. Cargar solo agrega, y nada se borra ni se modifica.
- **Aislamiento por cliente.** Cuatro filtros independientes basados en la identificación que trae cada documento ([decisión 0011](docs/decisiones/0011-filtros-entre-clientes.md)).
- **Lo que ve Claude.** Solo las respuestas de las herramientas, que se procesan como cualquier conversación con Claude. Claude no tiene acceso a los archivos ni a las bases.

Fuera de alcance: la seguridad del propio equipo del usuario, de Claude Desktop y de los servicios de Anthropic. Por ahora las bases no van cifradas: quien tenga acceso a la carpeta de datos puede leerlas.
