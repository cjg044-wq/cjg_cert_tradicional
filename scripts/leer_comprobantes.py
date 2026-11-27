#!/usr/bin/env python3
"""Lee comprobantes emitidos y los deja en un JSON normalizado.

Fuentes aceptadas (se pueden mezclar, se deduplican por tipo+PV+número):
  * PDF de comprobantes de ARCA (Factura / Nota de Crédito / Nota de Débito A, B, C),
    tal como los descarga "Comprobantes en línea". Se toma solo la hoja ORIGINAL.
  * Exportación de "Mis Comprobantes" emitidos (.xlsx o .csv).

Uso:
  python3 -I leer_comprobantes.py SALIDA.json ARCHIVO_O_CARPETA [...]

Salida: {"emisor": {...}, "comprobantes": [...], "avisos": [...]}
Cada comprobante: fecha (dd/mm/aaaa), cod, tipo ("11 - Factura C"), pv, nro,
importe (float, negativo en notas de crédito), desde/hasta (período facturado,
si figura), receptor, cond_iva_receptor, archivo.
"""
import csv, json, os, re, subprocess, sys
from datetime import date

TIPOS = {
    1: "Factura A", 2: "Nota de Débito A", 3: "Nota de Crédito A",
    6: "Factura B", 7: "Nota de Débito B", 8: "Nota de Crédito B",
    11: "Factura C", 12: "Nota de Débito C", 13: "Nota de Crédito C",
    19: "Factura E", 20: "Nota de Débito E", 21: "Nota de Crédito E",
    51: "Factura M", 52: "Nota de Débito M", 53: "Nota de Crédito M",
}
NC = {3, 8, 13, 21, 53}

avisos = []


def num_ar(s):
    s = s.strip().replace("$", "").replace(" ", "")
    if re.fullmatch(r"-?\d+(,\d+)?", s):          # 14424978,30
        return float(s.replace(",", "."))
    if re.fullmatch(r"-?[\d.]+,\d+", s):          # 14.424.978,30
        return float(s.replace(".", "").replace(",", "."))
    if re.fullmatch(r"-?[\d,]+\.\d+", s):         # 14,424,978.30
        return float(s.replace(",", ""))
    return float(s)


def fecha_ok(s):
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", s or "")
    if not m:
        return None
    d, mth, y = map(int, m.groups())
    try:
        return date(y, mth, d)
    except ValueError:
        return None


def leer_pdf(path):
    txt = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True).stdout
    # Solo la primera copia (ORIGINAL); ARCA repite DUPLICADO/TRIPLICADO.
    partes = re.split(r"\n\s*(?:DUPLICADO|TRIPLICADO)\s*\n", txt)
    t = partes[0]
    g = lambda rx: (re.search(rx, t) or [None, None])[1]
    cod = g(r"COD\.\s*0*(\d+)")
    if not cod:
        avisos.append(f"{os.path.basename(path)}: no parece un comprobante de ARCA, se omite")
        return None, None
    cod = int(cod)
    pv = int(g(r"Punto de Venta:\s*(\d+)"))
    nro = int(g(r"Comp\. Nro:\s*(\d+)"))
    fecha = g(r"Fecha de Emisi[oó]n:\s*(\d{2}/\d{2}/\d{4})")
    total = num_ar(g(r"Importe Total:\s*\$?\s*([\d.,]+)"))
    desde = g(r"Per[ií]odo Facturado Desde:\s*(\d{2}/\d{2}/\d{4})")
    hasta = g(r"Hasta:\s*(\d{2}/\d{2}/\d{4})")
    base = os.path.basename(path)
    # Corrección de años mal tipeados en el período (ej. 01/11/0226)
    if desde and not (fecha_ok(desde) and 2000 <= fecha_ok(desde).year <= 2100):
        if hasta and fecha_ok(hasta):
            avisos.append(f"{base}: período 'Desde' con año inválido ({desde}); se toma el año de 'Hasta'")
            desde = desde[:6] + hasta[6:]
        else:
            desde = None
    receptor = None
    m = re.search(r"Apellido y Nombre / Raz[oó]n Social:\s*([^\n]+)", t)
    if m:
        receptor = m.group(1).strip()
    conds = re.findall(r"Condici[oó]n frente al IVA:\s*([^\n]+?)(?:\s{2,}|$)", t, re.M)
    cond_rec = conds[1].strip() if len(conds) > 1 else None
    emisor = {
        "razon_social": (g(r"Raz[oó]n Social:\s*([^\n]+?)\s{2,}") or "").strip(),
        "domicilio_comercial": (g(r"Domicilio Comercial:\s*([^\n]+?)\s{2,}") or "").strip(),
        "cuit": g(r"CUIT:\s*(\d{11})"),
        "cond_iva": conds[0].strip() if conds else None,
        "inicio_actividades": g(r"Inicio de Actividades:\s*(\d{2}/\d{2}/\d{4})"),
    }
    items = re.findall(r"^\s{0,12}(\S[^\n]*?)\s{2,}\d+,\d{2}\s+(?:unidades|otras unidades|servicios)", t, re.M)
    comp = {
        "fecha": fecha, "cod": cod, "tipo": f"{cod} - {TIPOS.get(cod, 'Comprobante')}",
        "pv": pv, "nro": nro, "importe": -abs(total) if cod in NC else total,
        "desde": desde, "hasta": hasta, "receptor": receptor, "cond_iva_receptor": cond_rec,
        "detalle": items[0].strip() if items else None, "archivo": base,
    }
    return emisor, comp


def leer_tabla(path):
    """Exportación de Mis Comprobantes (xlsx/csv)."""
    rows = []
    if path.lower().endswith((".xlsx", ".xls")):
        import openpyxl
        ws = openpyxl.load_workbook(path, data_only=True).active
        rows = [[("" if c is None else c) for c in r] for r in ws.iter_rows(values_only=True)]
    else:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            sample = f.read(4096); f.seek(0)
            rows = list(csv.reader(f, delimiter=";" if sample.count(";") > sample.count(",") else ","))
    hi = next((i for i, r in enumerate(rows) if any(str(c).strip().lower() == "fecha" for c in r)), None)
    if hi is None:
        avisos.append(f"{os.path.basename(path)}: no encontré la fila de encabezados de Mis Comprobantes")
        return []
    head = [str(c).strip().lower() for c in rows[hi]]
    def col(*names):
        for n in names:
            for i, h in enumerate(head):
                if h.startswith(n):
                    return i
        return None
    cf, ct, cp, cn, ci = col("fecha"), col("tipo"), col("punto de venta"), col("número desde", "numero desde"), col("imp. total", "importe total")
    out = []
    for r in rows[hi + 1:]:
        if not r or cf is None or not str(r[cf]).strip():
            continue
        f = r[cf]
        if hasattr(f, "strftime"):
            f = f.strftime("%d/%m/%Y")
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(f)):
            y, m_, d = str(f).split("-"); f = f"{d}/{m_}/{y}"
        tipo = str(r[ct]).strip()
        cod = int(re.match(r"\s*(\d+)", tipo).group(1)) if re.match(r"\s*\d+", tipo) else 0
        imp = r[ci]
        imp = float(imp) if isinstance(imp, (int, float)) else num_ar(str(imp))
        out.append({"fecha": f, "cod": cod, "tipo": f"{cod} - {TIPOS.get(cod, tipo)}", "pv": int(float(r[cp])),
                    "nro": int(float(r[cn])), "importe": -abs(imp) if cod in NC else imp,
                    "desde": None, "hasta": None, "receptor": None, "cond_iva_receptor": None,
                    "detalle": None, "archivo": os.path.basename(path)})
    return out


def main():
    salida, fuentes = sys.argv[1], sys.argv[2:]
    files = []
    for s in fuentes:
        if os.path.isdir(s):
            for root, _, fs in os.walk(s):
                files += [os.path.join(root, f) for f in sorted(fs)]
        else:
            files.append(s)
    emisor, comps = None, {}
    for f in files:
        low = f.lower()
        if low.endswith(".pdf"):
            e, c = leer_pdf(f)
            if c:
                emisor = emisor or e
                comps[(c["cod"], c["pv"], c["nro"])] = c
        elif low.endswith((".xlsx", ".xls", ".csv")):
            for c in leer_tabla(f):
                comps.setdefault((c["cod"], c["pv"], c["nro"]), c)
    lista = sorted(comps.values(), key=lambda c: (fecha_ok(c["fecha"]) or date.min, c["pv"], c["nro"]))
    # Controles
    for c in lista:
        if c["cond_iva_receptor"] and "proveedor" in c["cond_iva_receptor"].lower():
            avisos.append(f"{c['tipo']} {c['pv']:05d}-{c['nro']:08d}: el receptor figura como '{c['cond_iva_receptor']}' (¿debería ser cliente?)")
    json.dump({"emisor": emisor, "comprobantes": lista, "avisos": avisos}, open(salida, "w"), ensure_ascii=False, indent=1)
    print(f"{len(lista)} comprobantes -> {salida}")
    for a in avisos:
        print("AVISO:", a)


if __name__ == "__main__":
    main()
