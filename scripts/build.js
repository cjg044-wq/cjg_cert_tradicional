const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType,
  AlignmentType, BorderStyle, ShadingType, ImageRun, PageBreak, LevelFormat,
  VerticalAlign, TableLayoutType, HeightRule,
} = require("docx");

// Uso: node build.js datos.json salida.docx [all|cert|anexo] [carpeta_assets]
// carpeta_assets debe contener firma_cjg.png (firma del contador).
const D = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = process.argv[3];
const ONLY = process.argv[4] || "all"; // all | cert | anexo
const ASSETS = process.argv[5] || process.env.CJG_ASSETS || (__dirname + "/../assets");

const FONT = "Tahoma";
const SZ = 20; // 10 pt
const NAVY = "44546A";
const firma = fs.readFileSync(ASSETS + "/firma_cjg.png");

// Firma del cliente: ancho máx. 190 px y alto máx. 120 px, respetando proporción (lee el encabezado PNG)
function firmaClienteRun(path) {
  const buf = fs.readFileSync(path);
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  const k = Math.min(190 / w, 120 / h);
  return new ImageRun({ type: "png", data: buf, transformation: { width: Math.round(w * k), height: Math.round(h * k) } });
}

const r = (text, o = {}) => new TextRun({ text, font: FONT, size: SZ, ...o });
const p = (children, o = {}) =>
  new Paragraph({ children: Array.isArray(children) ? children : [children], spacing: { before: 0, after: 0, line: 240 }, ...o });
const blank = () => p(r(""));
const just = (runs) => p(runs, { alignment: AlignmentType.JUSTIFIED });

const thin = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const thick = { style: BorderStyle.SINGLE, size: 12, color: "000000" };
const allB = (b) => ({ top: b, bottom: b, left: b, right: b });

// ---------- Certificación ----------
function cert() {
  const out = [];
  out.push(p(r("CERTIFICACIÓN DE CONTADOR PÚBLICO INDEPENDIENTE", { bold: true }), { alignment: AlignmentType.CENTER }));
  out.push(p(r("SOBRE DECLARACIÓN DE INGRESOS PERSONALES", { bold: true }), { alignment: AlignmentType.CENTER }));
  out.push(blank());
  out.push(p(r(`SEÑOR: ${D.nombre}`)));
  out.push(p(r(`DOMICILIO: ${D.domicilio}`)));
  out.push(p(r(`CUIL: ${D.cuit}`)));
  out.push(p(r(`LOCALIDAD: ${D.localidad}`)));
  out.push(blank());
  out.push(p(r("1-Identificación de la información objeto de la certificación", { bold: true })));
  out.push(just(r(
    `He sido contratado para emitir una certificación sobre la declaración de ingresos personales brutos preparada por ${D.nombre}, DNI ${D.dni}, CUIT ${D.cuit}, con domicilio real en la calle ${D.domicilio_real}, dedicado a la prestación de ${D.actividad}, referida a sus ingresos brutos por el período transcurrido entre el ${D.desde_txt} y el ${D.hasta_txt}, los que ascienden a $ ${D.total} (${D.total_letras}), la cual se adjunta firmada por mí al solo efecto de su identificación, para su presentación ante quien corresponda.`)));
  out.push(blank());
  out.push(just(r("La certificación se aplica a ciertas situaciones de hecho o comprobaciones especiales, a través de la constatación con registros contables y otra documentación de respaldo. Este trabajo profesional no constituye una auditoría ni una revisión y, por lo tanto, las manifestaciones del contador público no representan la emisión de un juicio técnico respecto de la información objeto de la certificación.")));
  out.push(blank());
  out.push(p(r("2-Responsabilidades del comitente", { bold: true })));
  out.push(just(r(`El ${D.trat} ${D.nombre} es responsable de la preparación y emisión de la declaración adjunta que presenta la información mencionada en la sección precedente.`)));
  out.push(blank());
  out.push(p(r("3-Responsabilidades del contador público", { bold: true })));
  out.push(just(r("Mi responsabilidad consiste en emitir una certificación sobre la información que se menciona en la primera sección. He llevado a cabo mi encargo de conformidad con las normas incluidas en el capítulo VI de la Resolución Técnica N° 37 de la Federación Argentina de Consejos Profesionales de Ciencias Económicas (FACPCE) y de las Resoluciones pertinentes del CPCE Cba. Dichas normas exigen que cumpla los requerimientos de ética, así como que planifique mi tarea.")));
  out.push(blank());
  out.push(p(r("4-Tarea realizada", { bold: true })));
  out.push(just(r("Mi tarea profesional se limitó a cotejar la información incluida en la declaración de ingresos mencionada en la primera sección de esta certificación con la siguiente documentación:")));
  for (const b of D.documentacion) {
    out.push(new Paragraph({
      numbering: { reference: "bul", level: 0 }, alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 0, after: 0, line: 240 }, children: [r(b, { italics: true })],
    }));
  }
  out.push(blank());

  // Tabla mensual
  const C1 = 1500, C2 = 2050;
  const hcell = (t, w, al = AlignmentType.CENTER) => new TableCell({
    width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: { type: ShadingType.CLEAR, fill: NAVY, color: "auto" }, borders: allB(thick),
    margins: { left: 60, right: 60 },
    children: [new Paragraph({ alignment: al, children: [new TextRun({ text: t, font: "Arial", size: 16, bold: true, color: "FFFFFF" })] })],
  });
  const vcell = (t, w, bold = false) => new TableCell({
    width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, borders: allB(thick),
    margins: { left: 60, right: 60 },
    children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: t, font: "Arial", size: 16, bold })] })],
  });
  const row = (cells, h = 330) => new TableRow({ height: { value: h, rule: HeightRule.ATLEAST }, cantSplit: true, children: cells });
  const rows = [row([hcell("Mes/Actividad", C1), hcell(D.columna, C2)], 450)];
  for (const m of D.meses) rows.push(row([hcell(m.mes, C1), vcell(m.importe, C2)]));
  out.push(new Table({ alignment: AlignmentType.CENTER, width: { size: C1 + C2, type: WidthType.DXA }, columnWidths: [C1, C2], layout: TableLayoutType.FIXED, rows }));
  out.push(blank());
  out.push(new Table({ alignment: AlignmentType.CENTER, width: { size: C1 + C2, type: WidthType.DXA }, columnWidths: [C1, C2], layout: TableLayoutType.FIXED,
    rows: [row([hcell("Total", C1), vcell(D.total, C2, true)])] }));

  const keep = { keepNext: true, keepLines: true };
  out.push(p(r(""), keep));
  out.push(p(r("5-Manifestación profesional", { bold: true }), keep));
  out.push(just(r(`Sobre la base de las tareas descriptas, CERTIFICO que los ingresos brutos declarados por el ${D.trat} ${D.nombre} identificados en el apartado 1-Identificación de la información objeto de la certificación, ascienden a $ ${D.total} (${D.total_letras}), y concuerdan con la documentación detallada en el apartado precedente.`)));
  out[out.length - 1] = new Paragraph({ alignment: AlignmentType.JUSTIFIED, keepNext: true, keepLines: true, spacing: { before: 0, after: 0, line: 240 },
    children: [r(`Sobre la base de las tareas descriptas, CERTIFICO que los ingresos brutos declarados por el ${D.trat} ${D.nombre} identificados en el apartado 1-Identificación de la información objeto de la certificación, ascienden a $ ${D.total} (${D.total_letras}), y concuerdan con la documentación detallada en el apartado precedente.`)] });
  out.push(p(r(""), keep));
  out.push(p(r(`Ciudad de Córdoba, Provincia de Córdoba, ${D.fecha_txt},`), { alignment: AlignmentType.RIGHT, ...keep }));
  out.push(p(r(""), keep));
  out.push(new Paragraph({ keepNext: true, keepLines: true, spacing: { before: 0, after: 0 }, children: [new ImageRun({ type: "png", data: firma, transformation: { width: 157, height: 93 } })] }));
  for (const [i, t] of ["Cristian Javier García", "Contador Público", "Universidad Nacional de Córdoba", "Matrícula 10-21827-5 CPCE Córdoba"].entries())
    out.push(p(r(t, { bold: true }), i < 3 ? keep : {}));
  return out;
}

// ---------- Anexo (declaración) ----------
function anexo() {
  const out = [];
  out.push(p(new TextRun({ text: "DECLARACIÓN DE INGRESOS PERSONALES", font: "Arial", size: 28, bold: true }), { alignment: AlignmentType.CENTER }));
  out.push(blank());
  out.push(p(r(`${D.lugar_decl}, ${D.fecha_txt}`)));
  out.push(blank());
  out.push(p(r("Por medio de la presente, solicito emisión de una certificación de ingresos personales.")));
  out.push(just(r(`A continuación, detallo los ingresos en moneda nominal, que he obtenido durante el período transcurrido entre el ${D.desde_txt} y el ${D.hasta_txt}, proveniente de mi actividad de prestación de ${D.actividad}:`)));
  out.push(blank());

  const W = [1050, 1750, 1400, 1340, 1340];
  const tot = W.reduce((a, b) => a + b, 0);
  const H = ["Fecha", "Tipo", "Punto de Venta", "Número Desde", "Imp. Total"];
  const hc = (t, w) => new TableCell({ width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    shading: { type: ShadingType.CLEAR, fill: NAVY, color: "auto" }, borders: allB(thin), margins: { left: 60, right: 60 },
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: t, font: "Arial", size: 16, bold: true, color: "FFFFFF" })] })] });
  const dc = (t, w, al) => new TableCell({ width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, borders: allB(thin),
    margins: { left: 60, right: 60 },
    children: [new Paragraph({ alignment: al, children: [new TextRun({ text: t, font: "Arial", size: 16 })] })] });
  const rows = [new TableRow({ height: { value: 480, rule: HeightRule.ATLEAST }, children: H.map((h, i) => hc(h, W[i])) })];
  for (const c of D.comprobantes) {
    rows.push(new TableRow({ height: { value: 240, rule: HeightRule.ATLEAST }, children: [
      dc(c.fecha, W[0], AlignmentType.LEFT), dc(c.tipo, W[1], AlignmentType.LEFT),
      dc(c.pv, W[2], AlignmentType.RIGHT), dc(c.nro, W[3], AlignmentType.RIGHT), dc(c.importe, W[4], AlignmentType.RIGHT)] }));
  }
  out.push(new Table({ alignment: AlignmentType.CENTER, width: { size: tot, type: WidthType.DXA }, columnWidths: W, layout: TableLayoutType.FIXED, rows }));
  out.push(p(r(""), { keepNext: true }));

  // Bloque firma del cliente (izq) + TOTAL (der)
  const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  const noB = allB(none);
  const FW = 4200, GAP = tot - FW - W[3] - W[4] >= 0 ? (tot - FW - W[3] - W[4]) : 0;
  const leftOffset = 0;
  const sigCell = new TableCell({ width: { size: FW, type: WidthType.DXA }, borders: noB,
    children: [
      ...(D.firma_cliente ? [new Paragraph({ alignment: AlignmentType.CENTER, children: [firmaClienteRun(D.firma_cliente)] })]
        : [0,1,2].map(() => new Paragraph({ children: [new TextRun({ text: "", font: "Arial", size: 16 })] }))),
      new Paragraph({ border: { top: { style: BorderStyle.SINGLE, size: 4, color: "000000", space: 1 } },
        children: [new TextRun({ text: "Firma: " + D.nombre, font: "Arial", size: 18 })] }),
      new Paragraph({ children: [new TextRun({ text: "CUIT " + D.cuit, font: "Arial", size: 18 })] }),
    ] });
  const gapCell = new TableCell({ width: { size: GAP, type: WidthType.DXA }, borders: noB, children: [new Paragraph("")] });
  const tl = new TableCell({ width: { size: W[3], type: WidthType.DXA }, borders: allB(thin), margins: { left: 60, right: 60 },
    children: [new Paragraph({ children: [new TextRun({ text: "TOTAL", font: "Arial", size: 16 })] })] });
  const tv = new TableCell({ width: { size: W[4], type: WidthType.DXA }, borders: allB(thin), margins: { left: 60, right: 60 },
    children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: D.total, font: "Arial", size: 16 })] })] });
  const totCell = new TableCell({ width: { size: W[3] + W[4], type: WidthType.DXA }, borders: noB, margins: { left: 0, right: 0 },
    children: [new Table({ width: { size: W[3] + W[4], type: WidthType.DXA }, columnWidths: [W[3], W[4]], layout: TableLayoutType.FIXED,
      rows: [new TableRow({ children: [tl, tv] })] }), new Paragraph("")] });
  out.push(new Table({ alignment: AlignmentType.CENTER, width: { size: tot, type: WidthType.DXA }, columnWidths: [FW, GAP, W[3] + W[4]], layout: TableLayoutType.FIXED,
    borders: { top: none, bottom: none, left: none, right: none, insideHorizontal: none, insideVertical: none },
    rows: [new TableRow({ cantSplit: true, children: [sigCell, gapCell, totCell] })] }));

  out.push(blank()); out.push(blank()); out.push(blank());
  const keep = { keepNext: true, keepLines: true };
  out.push(p(new TextRun({ text: `Firmado por mí a los efectos de su identificación con mi certificación de fecha ${D.fecha}`, font: "Arial", size: 16 }), keep));
  out.push(new Paragraph({ keepNext: true, keepLines: true, spacing: { before: 0, after: 0 }, children: [new ImageRun({ type: "png", data: firma, transformation: { width: 157, height: 93 } })] }));
  for (const [i, t] of ["Cristian Javier García", "Contador Público", "Universidad Nacional de Córdoba", "Matrícula 10-21827-5 CPCE Córdoba"].entries())
    out.push(p(r(t, { bold: true }), i < 3 ? keep : {}));
  return out;
}

let children = [];
if (ONLY === "all" || ONLY === "cert") children = children.concat(cert());
if (ONLY === "all") children.push(new Paragraph({ children: [new PageBreak()] }));
if (ONLY === "all" || ONLY === "anexo") children = children.concat(anexo());

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: SZ } } } },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\uF0B7", alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 720, hanging: 360 } }, run: { font: "Symbol" } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1180, bottom: 1134, left: 1701, right: 610 } } },
    children,
  }],
});
Packer.toBuffer(doc).then((b) => fs.writeFileSync(OUT, b));
