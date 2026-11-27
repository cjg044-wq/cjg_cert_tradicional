#!/usr/bin/env bash
# Genera los 3 entregables a partir de datos.json:
#   CERTIFICACION_DE_INGRESOS_<APELLIDO>_<AAAA_MM>.docx        (certificación + declaración, editable)
#   CERTIFICACION_DE_INGRESOS_<APELLIDO>_<AAAA_MM>.pdf         (certificación, hojas 1-2)
#   CERTIFICACION_DE_INGRESOS_<APELLIDO>_<AAAA_MM> - ANEXO.pdf (declaración del cliente + cierre del contador)
# Uso: generar.sh datos.json CARPETA_SALIDA CARPETA_ASSETS
set -euo pipefail
DATOS="$(realpath "$1")"; OUT="$(realpath -m "$2")"; ASSETS="$(realpath "$3")"
HERE="$(cd "$(dirname "$0")" && pwd)"
SOFFICE="${SOFFICE:-/mnt/skills/public/docx/scripts/office/soffice.py}"
mkdir -p "$OUT"; TMP="$(mktemp -d)"
APELLIDO=$(python3 -I -c "import json,sys,unicodedata;n=json.load(open(sys.argv[1]))['nombre'].split()[0];print(unicodedata.normalize('NFKD',n).encode('ascii','ignore').decode().upper())" "$DATOS")
PER=$(python3 -I -c "import json,sys;print(json.load(open(sys.argv[1]))['periodo_archivo'])" "$DATOS")
BASE="CERTIFICACION_DE_INGRESOS_${APELLIDO}_${PER}"
conv() {  # docx -> pdf (LibreOffice) -> A4 escalado como el original de Word
  if [ -f "$SOFFICE" ]; then python3 "$SOFFICE" --headless --convert-to pdf --outdir "$TMP" "$1" >/dev/null 2>&1
  else soffice --headless --convert-to pdf --outdir "$TMP" "$1" >/dev/null 2>&1; fi
  python3 -I "$HERE/scale_a4.py" "${1%.docx}.pdf" "$2"
}
for k in all cert anexo; do
  node "$HERE/build.js" "$DATOS" "$TMP/$k.docx" "$k" "$ASSETS"
  (cd "$TMP" && zip -d "$k.docx" '*/' >/dev/null 2>&1 || true)
done
cp "$TMP/all.docx" "$OUT/$BASE.docx"
conv "$TMP/cert.docx" "$OUT/$BASE.pdf"
conv "$TMP/anexo.docx" "$OUT/$BASE - ANEXO.pdf"
conv "$TMP/all.docx" "$TMP/preview.pdf"
PREV="${PREVIEW_DIR:-/tmp/cjg_preview}"; rm -rf "$PREV"; mkdir -p "$PREV"; pdftoppm -r 70 -png "$TMP/preview.pdf" "$PREV/p" 2>/dev/null || true; echo "Vista previa: $PREV"
echo "Páginas certificación: $(pdfinfo "$OUT/$BASE.pdf" | awk '/Pages/{print $2}') · anexo: $(pdfinfo "$OUT/$BASE - ANEXO.pdf" | awk '/Pages/{print $2}')"
ls -1 "$OUT"
rm -rf "$TMP"
