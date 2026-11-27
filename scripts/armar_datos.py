#!/usr/bin/env python3
"""Arma el datos.json que usa build.js a partir de los comprobantes y los datos del cliente.

Uso:
  python3 -I armar_datos.py comprobantes.json cliente.json datos.json

cliente.json (ver ejemplo/cliente_ejemplo.json):
  nombre            "Apellido Nombres" (como en el modelo, tipo título)
  trat              "Sr." / "Sra."
  dni, cuit         "20.123.456", "20-20123456-3"
  domicilio         calle y número (encabezado)
  localidad         "Santo Tomé, Provincia de Corrientes" (encabezado)
  domicilio_real    texto completo para el punto 1 (calle, barrio/entre calles, localidad, provincia)
  actividad         descripción de la actividad según constancia ARCA (en MAYÚSCULAS)
  columna           título de la columna del cuadro mensual (ej. "Servicios Profesionales")
  lugar_decl        lugar de la declaración del cliente (por defecto su localidad)
  fecha             dd/mm/aaaa de la certificación (por defecto hoy)
  criterio_mes      "periodo" (mes del período facturado; default) o "emision" (mes de la fecha de emisión)
  desde, hasta      opcionales: fuerzan el período certificado (dd/mm/aaaa)
  firma_cliente     opcional: ruta al PNG de la firma del cliente
"""
import json, sys, calendar
from datetime import date

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
MES_ABR = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

UNI = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve", "diez",
       "once", "doce", "trece", "catorce", "quince", "dieciséis", "diecisiete", "dieciocho",
       "diecinueve", "veinte", "veintiuno", "veintidós", "veintitrés", "veinticuatro",
       "veinticinco", "veintiséis", "veintisiete", "veintiocho", "veintinueve"]
DEC = ["", "", "", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
CEN = ["", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos", "seiscientos",
       "setecientos", "ochocientos", "novecientos"]


def _cien(n, apocope):
    """0..999. apocope=True -> 'un'/'veintiún'/'y un' (antes de mil/millones)."""
    if n == 0:
        return ""
    if n == 100:
        return "cien"
    c, r = divmod(n, 100)
    partes = [CEN[c]] if c else []
    if r:
        if r < 30:
            w = UNI[r]
            if apocope and r == 1:
                w = "un"
            elif apocope and r == 21:
                w = "veintiún"
        else:
            d, u = divmod(r, 10)
            w = DEC[d] + (" y " + ("un" if (apocope and u == 1) else UNI[u]) if u else "")
        partes.append(w)
    return " ".join(partes)


def en_letras(n):
    n = int(n)
    if n == 0:
        return "cero"
    mill, resto = divmod(n, 1_000_000)
    miles, unid = divmod(resto, 1000)
    out = []
    if mill:
        out.append("un millón" if mill == 1 else en_letras_miles(mill) + " millones")
    if miles:
        out.append("mil" if miles == 1 else _cien(miles, True) + " mil")
    if unid:
        out.append(_cien(unid, False))
    return " ".join(out)


def en_letras_miles(n):
    """Para la cantidad de millones (hasta 999.999), con apócope: 'cincuenta y un millones'."""
    miles, unid = divmod(n, 1000)
    out = []
    if miles:
        out.append("mil" if miles == 1 else _cien(miles, True) + " mil")
    if unid:
        out.append(_cien(unid, True))
    return " ".join(out)


def monto_letras(x):
    entero = int(round(abs(x) * 100)) // 100
    cent = int(round(abs(x) * 100)) % 100
    return f"pesos {en_letras(entero)} con {cent:02d} centavos"


def fmt(x):
    s = f"{abs(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if x < 0 else "") + s


def d(s):
    dd, mm, yy = map(int, s.split("/"))
    return date(yy, mm, dd)


def fecha_larga(x):
    return f"{x.day:02d} de {MESES[x.month - 1]} de {x.year}"


def main():
    comp = json.load(open(sys.argv[1]))
    cli = json.load(open(sys.argv[2]))
    lista = comp["comprobantes"]
    if not lista:
        sys.exit("No hay comprobantes")
    criterio = cli.get("criterio_mes", "periodo")

    # Mes de imputación de cada comprobante
    def mes(c):
        if criterio == "periodo" and c.get("desde"):
            x = d(c["desde"])
        else:
            x = d(c["fecha"])
        return (x.year, x.month)

    meses = {}
    for c in lista:
        meses[mes(c)] = meses.get(mes(c), 0.0) + c["importe"]
    total = round(sum(c["importe"] for c in lista), 2)

    # Período certificado
    if cli.get("desde") and cli.get("hasta"):
        desde, hasta = d(cli["desde"]), d(cli["hasta"])
    elif criterio == "periodo" and all(c.get("desde") and c.get("hasta") for c in lista):
        desde = min(d(c["desde"]) for c in lista)
        hasta = max(d(c["hasta"]) for c in lista)
    else:  # por emisión: meses completos, como en certificaciones con muchas facturas
        f = [d(c["fecha"]) for c in lista]
        a, b = min(f), max(f)
        desde = date(a.year, a.month, 1)
        hasta = date(b.year, b.month, calendar.monthrange(b.year, b.month)[1])

    # Documentación respaldatoria: un renglón por clase de comprobante (facturas / notas de crédito / débito)
    def rango(cs):
        por_pv = {}
        for c in cs:
            por_pv.setdefault(c["pv"], []).append(c["nro"])
        letra = cs[0]["tipo"].split()[-1]
        partes = []
        for pv in sorted(por_pv):
            ns = sorted(por_pv[pv])
            if len(ns) == 1:
                partes.append(f"n° {letra}-{pv:05d}-{ns[0]:08d}")
            else:
                partes.append(f"desde el n° {letra}-{pv:05d}-{ns[0]:08d} hasta el n° {letra}-{pv:05d}-{ns[-1]:08d}")
        return ", ".join(partes[:-1]) + (" y " if len(partes) > 1 else "") + partes[-1]

    doc = []
    for clase, rotulo in [("Factura", "Facturas"), ("Nota de Débito", "Notas de débito"), ("Nota de Crédito", "Notas de crédito")]:
        cs = [c for c in lista if (" - " + clase) in c["tipo"]]
        if cs:
            doc.append(f"{rotulo} emitidas por el {cli.get('trat', 'Sr.')} {cli['nombre']}, {rango(cs)}.")

    fecha = d(cli["fecha"]) if cli.get("fecha") else date.today()
    datos = {
        "nombre": cli["nombre"], "trat": cli.get("trat", "Sr."), "dni": cli["dni"], "cuit": cli["cuit"],
        "domicilio": cli["domicilio"], "localidad": cli["localidad"], "domicilio_real": cli["domicilio_real"],
        "actividad": cli["actividad"], "columna": cli.get("columna", "Servicios Profesionales"),
        "desde_txt": fecha_larga(desde), "hasta_txt": fecha_larga(hasta),
        "total": fmt(total), "total_letras": monto_letras(total),
        "documentacion": doc,
        "meses": [{"mes": f"{MES_ABR[m - 1]}-{str(y)[2:]}", "importe": fmt(v)} for (y, m), v in sorted(meses.items())],
        "fecha_txt": f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}",
        "fecha": fecha.strftime("%d/%m/%Y"),
        "lugar_decl": cli.get("lugar_decl") or cli["localidad"].split(",")[0],
        "comprobantes": [{"fecha": c["fecha"], "tipo": c["tipo"], "pv": str(c["pv"]), "nro": str(c["nro"]),
                          "importe": (fmt(c["importe"]).replace("-", "- ") if c["importe"] < 0 else fmt(c["importe"]))}
                         for c in lista],
        "periodo_archivo": f"{hasta.year}_{hasta.month:02d}",
    }
    if cli.get("firma_cliente"):
        datos["firma_cliente"] = cli["firma_cliente"]
    json.dump(datos, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
    print(f"Total {datos['total']} ({datos['total_letras']})")
    print(f"Período: {datos['desde_txt']} al {datos['hasta_txt']}")
    for m in datos["meses"]:
        print(f"  {m['mes']}: {m['importe']}")


if __name__ == "__main__":
    main()
