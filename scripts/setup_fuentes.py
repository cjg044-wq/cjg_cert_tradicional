#!/usr/bin/env python3
"""Deja disponible Tahoma (normal y negrita) para que LibreOffice genere el PDF igual que Word.

  * Tahoma normal: clon métrico de Wine (paquete fonts-wine, libre).
  * Tahoma negrita: el clon de Wine no tiene negrita real, así que se usa la Tahoma Bold
    original. No se versiona en el repo (es de Microsoft): se toma de la carpeta de assets
    (tahoma_bold.ttf) o se extrae de una certificación anterior en PDF hecha con Word
    (cubre exactamente los textos en negrita fijos de la certificación).

Uso:
  python3 -I setup_fuentes.py CARPETA_ASSETS [CERTIFICACION_ANTERIOR.pdf]
Si se pasa el PDF y no existe tahoma_bold.ttf en assets, lo extrae y lo guarda ahí.
"""
import os, re, shutil, subprocess, sys

ASSETS = sys.argv[1]
REF = sys.argv[2] if len(sys.argv) > 2 else None
FONTS = os.path.expanduser("~/.fonts")
os.makedirs(FONTS, exist_ok=True)

# 1) Tahoma normal (Wine)
wine = "/usr/share/wine/fonts/tahoma.ttf"
if not os.path.exists(wine):
    subprocess.run("apt-get install -y fonts-wine >/dev/null 2>&1 || (apt-get update >/dev/null 2>&1 && apt-get install -y fonts-wine >/dev/null 2>&1)",
                   shell=True)
if not os.path.exists(wine):
    sys.exit("No pude instalar fonts-wine (Tahoma normal).")
shutil.copy(wine, os.path.join(FONTS, "tahoma.ttf"))

# 2) Tahoma negrita
bold = os.path.join(ASSETS, "tahoma_bold.ttf")
if not os.path.exists(bold):
    if not REF:
        sys.exit(f"Falta {bold}. Pasá una certificación anterior en PDF (hecha con Word) para extraerla.")
    import pypdf
    from fontTools.ttLib import TTFont
    from fontTools.ttLib.tables._c_m_a_p import cmap_format_4
    import io
    r = pypdf.PdfReader(REF)
    data, tu = None, {}
    for p in r.pages:
        for _, v in p["/Resources"]["/Font"].items():
            v = v.get_object()
            if "Tahoma,Bold" not in v["/BaseFont"] and "Tahoma-Bold" not in v["/BaseFont"]:
                continue
            fd = v["/FontDescriptor"].get_object()
            data = data or fd["/FontFile2"].get_object().get_data()
            cm = v["/ToUnicode"].get_object().get_data().decode("latin1")
            for blk in re.findall(r"beginbfchar(.*?)endbfchar", cm, re.S):
                for a, b in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
                    tu[int(a, 16)] = chr(int(b, 16))
            for blk in re.findall(r"beginbfrange(.*?)endbfrange", cm, re.S):
                for a, b, c in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
                    for i in range(int(a, 16), int(b, 16) + 1):
                        tu[i] = chr(int(c, 16) + i - int(a, 16))
        if data:
            break
    if not data:
        sys.exit("El PDF de referencia no tiene Tahoma Bold embebida.")
    f = TTFont(io.BytesIO(data))
    sym = [t for t in f["cmap"].tables if t.platformID == 3][0].cmap
    uni = {ord(tu[code & 0xFF]): g for code, g in sym.items() if (code & 0xFF) in tu}
    st = cmap_format_4(4); st.platformID = 3; st.platEncID = 1; st.language = 0; st.cmap = uni
    f["cmap"].tables = [st]
    nm = f["name"]; nm.names = []
    for i, s in [(1, "Tahoma"), (2, "Bold"), (4, "Tahoma Bold"), (6, "Tahoma-Bold")]:
        nm.setName(s, i, 3, 1, 0x409)
    f["post"].formatType = 3.0
    f["OS/2"].usWeightClass = 700; f["OS/2"].fsSelection = 0x20; f["head"].macStyle = 1
    f.save(bold)
    print("Tahoma Bold extraída a", bold, "· caracteres:", "".join(sorted(chr(u) for u in uni)))
from fontTools.ttLib import TTFont as _TT
_f = _TT(bold)  # asegura que fontconfig la reconozca como negrita
_f["OS/2"].usWeightClass = 700; _f["OS/2"].fsSelection = 0x20; _f["head"].macStyle = 1
_f.save(os.path.join(FONTS, "tahomabd.ttf"))
subprocess.run(["fc-cache", "-f"], capture_output=True)
print(subprocess.run(["fc-match", "Tahoma:bold"], capture_output=True, text=True).stdout.strip())
