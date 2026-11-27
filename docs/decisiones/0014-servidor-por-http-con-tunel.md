# 0014 — Servidor por HTTP detrás de un túnel, para claude.ai y el celular

Fecha: 2026-11-26

## Contexto

El servidor solo hablaba por stdio, así que solo servía en Claude Desktop o Claude Code del mismo equipo. Para usarlo a diario desde claude.ai o la app del celular hace falta un **conector personalizado**: Claude se conecta desde la nube de Anthropic a una URL pública por HTTPS, en el puerto 443, con transporte Streamable HTTP ([guía de conectores](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)).

Subir las bases a un servidor en la nube rompería la garantía principal del README ("tus facturas no salen del equipo") y pondría datos tributarios de terceros en manos de otro proveedor. Se buscó una opción gratuita que no la rompa ([issue #21](https://github.com/RafaGM1108/auditor-dian-core/issues/21)).

## Decisión

- **El servidor sigue en el equipo del contador.** `auditor mcp --http` lo sirve por Streamable HTTP escuchando solo en `127.0.0.1`. Un túnel lo expone en una URL pública.
- **Túnel recomendado: Tailscale Funnel.** Es gratis, da una URL fija `*.ts.net` en el puerto 443 y el TLS termina en el propio equipo, así que nadie en medio ve la URL ni las respuestas.
- **La URL lleva un secreto de 256 bits** (`/mcp/<token>`); cualquier otra ruta responde 404. El token se crea una vez en la carpeta de datos con permisos 600, o se toma de `AUDITOR_DIAN_TOKEN`. Nunca se imprime: el comando dice dónde leerlo, y el registro de acceso de uvicorn lo muestra como `<token>` (*corregido el 2026-11-26*: antes cada pedido lo escribía completo).
- **Protección contra DNS rebinding activa**: solo se aceptan el dominio del túnel (`--dominio`) y localhost. El SDK la deja apagada si no se configura.
- **Sin estado entre pedidos** (`stateless_http`): reiniciar el servidor no rompe el conector.

## Alternativas descartadas

- **Token en un encabezado (`Authorization`)**: es lo ideal, pero en claude.ai los *Request headers* de un conector están en beta y solo para algunas organizaciones. El conector sin inicio de sesión funciona en todos los planes, incluido Free (un conector personalizado).
- **OAuth**: lo soporta claude.ai, pero exige un servidor de autorización. Es demasiado para un solo usuario; se revisará si se ofrece a varios contadores.
- **Cloudflare Tunnel**: también es gratis, pero termina el TLS en Cloudflare, que vería la URL con el token, y una URL fija exige tener un dominio propio.
- **Servidor en la nube** (VPS, Cloud Run): saca las bases del equipo y cuesta mantenerlo. Queda como opción para un plan Team, con cifrado de las bases.

## Consecuencias

- El equipo debe estar encendido para que Claude responda desde otro lugar.
- **Quien tenga la URL completa puede usar todas las herramientas**, incluidas las que cargan archivos del equipo y crean Excel. La URL es una contraseña: no se comparte. Para cambiarla basta con borrar `token-mcp` y reiniciar el servidor.
- Las respuestas de las herramientas (cifras, CUFE, nombres y NIT de proveedores) pasan por Anthropic igual que en Claude Desktop. Las bases y los archivos se quedan en el equipo.
