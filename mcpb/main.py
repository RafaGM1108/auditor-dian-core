"""Arranque del servidor MCP dentro de la extensión de Claude Desktop (.mcpb, tipo uv).

Desktop ejecuta `uv run server/main.py` en la carpeta de la extensión; uv instala `core` desde el
wheel que viaja en el paquete. Equivale a `auditor mcp`, plugins incluidos.
"""

from auditor_dian.cli import app

app(["mcp"])
