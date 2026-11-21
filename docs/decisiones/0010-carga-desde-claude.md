# 0010 — Carga de facturas desde Claude

Fecha: 2026-11-20

## Contexto

Para que un contador use Auditor DIAN y dé retroalimentación basta con instalar la extensión en Claude Desktop. Pero hasta ahora crear un cliente e ingerir las facturas solo se podía por la terminal (`auditor clientes crear`, `auditor ingerir`), y el servidor MCP era de solo lectura (decisión 0007). Un usuario no técnico instalaba la extensión y no tenía cómo cargar nada.

## Decisión

- Dos herramientas MCP que escriben: `crear_cliente` e `ingerir_facturas`. Usan el mismo código que la CLI.
- **Solo agregan.** Ninguna herramienta borra ni modifica documentos: un archivo ya cargado se salta por su SHA-256 y un CUFE repetido no se duplica (SPEC §6). Se anuncian con `readOnlyHint=false` y `destructiveHint=false`, para que el cliente MCP pida confirmación si así está configurado.
- `ingerir_facturas` acepta un ZIP, un XML o una carpeta. Si la base está abierta por otro programa (por ejemplo, una ingesta por terminal), explica el motivo.
- **El usuario no escribe rutas ni formatos** (*cambiado el 2026-11-20*: antes se pedía ruta absoluta y NIT solo con dígitos). Se asume un usuario sin conocimientos técnicos:
  - Una ruta relativa ("facturas enero", "Descargas/facturas enero") se busca en la carpeta personal y en Descargas, Escritorio y Documentos, en español o inglés y sin importar mayúsculas. `exportar_informe` hace lo mismo con el destino y agrega `.xlsx` si falta.
  - `ingerir_por_cliente` sin ruta revisa la carpeta de Descargas, que es donde quedan los ZIP del correo: "carga mis facturas" basta.
  - El NIT o la cédula se aceptan como los escriba el usuario: con 'NIT' o 'C.C.', puntos, comas, espacios, guion, con o sin dígito de verificación. El DV se quita si va tras un guion, o si sobra por la cantidad de dígitos y es el correcto según el algoritmo de la DIAN (módulo 11): un NIT de empresa tiene 9 dígitos y empieza por 8 o 9, y una cédula tiene a lo sumo 10. Si aún queda en duda (p. ej. una cédula de 8 dígitos más su DV), se usa el cliente ya registrado sin ese dígito. La identificación que viene en el XML no se interpreta: se compara exacta ("EXT-000123" no es el cliente 000123).
  - Las instrucciones del servidor le piden a Claude no pedir rutas, no mostrar nombres de herramientas ni JSON y hablar en lenguaje sencillo.
- `ingerir_por_cliente` reparte una carpeta con facturas de varios clientes según la identificación del comprador (adquirente) de cada archivo. Solo carga en clientes ya creados: un comprador desconocido puede ser un error o alguien que no es cliente, así que no se crea solo; se informa con su nombre para que el usuario decida. Un archivo con documentos de varios compradores, sin documentos legibles o con un comprador sin NIT ni cédula (p. ej. exportaciones) queda sin asignar, con el motivo.
- Saber si un cliente ya está registrado: `listar_clientes` busca por parte del NIT o del nombre (sin importar mayúsculas, tildes ni puntos) y `historial_cliente` muestra sus documentos por mes de emisión y cada carga. `crear_cliente` sobre un cliente existente no falla: devuelve su historial sin cambiar nada, y al crear uno nuevo avisa si otro cliente tiene el mismo nombre (posible NIT mal escrito). *Agregado el 2026-11-20.*
- Herramienta `diagnostico`, de solo lectura, para reportar problemas: versión, carpeta de datos, plugins y, por cliente, conteos, última carga y advertencias de lectura. No trae montos ni contenido de las facturas, para que el usuario pueda compartirlo.
- Las consultas siguen abriendo la base en solo lectura.

## Alternativas descartadas

- **Mantener la carga solo por terminal**: exige instalar `uv` y usar la consola, lo que deja fuera a la mayoría de contadores.
- **Herramientas para borrar clientes o documentos**: no hacen falta para usarlo; un error de carga se corrige creando el cliente de nuevo en otra carpeta. Se descartan para que el agente no pueda perder datos.
- **Leer directo del correo**: es Pro v2 (fuera de alcance).

## Consecuencias

- El principio "solo lectura" del SPEC ahora aplica frente a la DIAN y a las consultas; la base del cliente puede crecer desde Claude.
- La extensión cambia de descripción: ya no dice "solo lectura" sino "nada se borra ni se modifica".
