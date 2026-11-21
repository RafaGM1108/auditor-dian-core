#!/usr/bin/env bash
# Arma dist/auditor-dian-<versión>.mcpb: extensión de Claude Desktop con core, el logo y el
# manifiesto de mcpb/. Requiere uv y npx (para validar y empaquetar con @anthropic-ai/mcpb).
#
#   --desarrollo  en vez de copiar core en el paquete, lo instala en modo editable desde este
#                 repositorio: cada cambio se ve al reiniciar la extensión, sin reinstalarla.
#                 Solo sirve en esta máquina (lleva la ruta absoluta del repositorio).
#   --desarrollo RUTA...  además instala en modo editable cada plugin cuyo repositorio esté en
#                 RUTA (p. ej. ../auditor-dian-pro), para ver sus herramientas en Desktop.
set -euo pipefail
cd "$(dirname "$0")/.."

version=$(uv version --short)
nombre="auditor-dian-$version"
trabajo=$(mktemp -d)
trap 'rm -rf "$trabajo"' EXIT
mkdir -p "$trabajo/server" dist

dependencias='"auditor-dian-core"'
fuentes=""
if [[ "${1:-}" == "--desarrollo" ]]; then
  fuente="{ path = \"$PWD\", editable = true }"
  for plugin in "${@:2}"; do
    ruta=$(cd "$plugin" && pwd)
    paquete=$(python3 -c 'import sys, tomllib; print(tomllib.load(open(sys.argv[1], "rb"))["project"]["name"])' "$ruta/pyproject.toml")
    dependencias="$dependencias, \"$paquete\""
    fuentes="$fuentes$paquete = { path = \"$ruta\", editable = true }"$'\n'
  done
  nombre="$nombre-desarrollo"
  sed -e "s/\"VERSION\"/\"$version\"/" -e 's/"display_name": "Auditor DIAN"/"display_name": "Auditor DIAN (desarrollo)"/' \
    mcpb/manifest.json > "$trabajo/manifest.json"
else
  uv build -q --wheel -o "$trabajo/server"
  fuente="{ path = \"server/$(cd "$trabajo/server" && ls auditor_dian_core-*.whl)\" }"
  sed "s/\"VERSION\"/\"$version\"/" mcpb/manifest.json > "$trabajo/manifest.json"
fi
cp mcpb/main.py "$trabajo/server/main.py"
cp src/auditor_dian/logo.png "$trabajo/icon.png"
cp LICENSE "$trabajo/LICENSE"
cat > "$trabajo/pyproject.toml" <<TOML
[project]
name = "auditor-dian-extension"
version = "$version"
requires-python = ">=3.11"
dependencies = [$dependencias]

[tool.uv.sources]
auditor-dian-core = $fuente
$fuentes
TOML

npx -y @anthropic-ai/mcpb@2.1.2 validate "$trabajo/manifest.json"
npx -y @anthropic-ai/mcpb@2.1.2 pack "$trabajo" "dist/$nombre.mcpb"
