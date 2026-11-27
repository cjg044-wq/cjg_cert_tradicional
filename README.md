# cjg_cert_tradicional

Skill **`cjg-cert-tradicional`** del estudio contable CJG: arma la certificación de ingresos tradicional (RT 37 cap. VI — CPCE Córdoba) de un cliente a partir de sus comprobantes emitidos en ARCA.

Entregables: Word editable + PDF de la certificación + PDF del anexo (declaración de ingresos del cliente con el cierre firmado por el contador). Las instrucciones completas están en [`SKILL.md`](SKILL.md).

## Estructura

| Archivo | Qué hace |
|---|---|
| `SKILL.md` | Instrucciones de la skill: carpetas origen/destino, datos, criterios y controles |
| `scripts/leer_comprobantes.py` | Lee PDFs de ARCA y/o la exportación de Mis Comprobantes → `comprobantes.json` |
| `scripts/armar_datos.py` | Comprobantes + datos del cliente → `datos.json` (período, cuadro mensual, monto en letras, documentación) |
| `scripts/build.js` | Genera el .docx (certificación, declaración o ambos) con el formato del modelo |
| `scripts/generar.sh` | Corre todo: .docx + PDF de certificación + PDF de anexo, escalados a A4 |
| `scripts/scale_a4.py` | Escala el PDF (carta) a A4 como el original impreso con PDFCreator |
| `scripts/setup_fuentes.py` | Instala Tahoma (normal: clon Wine; negrita: desde assets privados o una certificación anterior) |
| `scripts/limpiar_firma.py` | Recorta la foto de una firma y le saca el fondo |
| `ejemplo/cliente_ejemplo.json` | Datos de cliente ficticios de ejemplo |

## Assets privados (no se versionan)

Este repo es público: la firma del contador y la fuente Tahoma Bold viven en
`G:\Mi unidad\Claude - Skills\cjg-cert-tradicional\` (`firma_cjg.png`, `tahoma_bold.ttf`).

## Uso rápido

```bash
S=scripts
python3 -I $S/setup_fuentes.py /ruta/assets
python3 -I $S/leer_comprobantes.py comprobantes.json carpeta_facturas/
python3 -I $S/armar_datos.py comprobantes.json cliente.json datos.json
$S/generar.sh datos.json salida/ /ruta/assets
```

Requiere: Python 3 (pypdf, fontTools, Pillow, numpy, openpyxl), Node (`docx`), LibreOffice, poppler-utils.
