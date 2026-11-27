---
name: cjg-cert-tradicional
description: Arma la certificación de ingresos tradicional (RT 37 cap. VI, CPCE Cba.) de un cliente a partir de sus facturas emitidas — Word + PDF de la certificación + PDF del anexo con la declaración — tomando la documentación de la carpeta que indique Cristian y guardando lo generado en la carpeta de destino que indique. Usar con /cjg-cert-tradicional.
---

# cjg-cert-tradicional — Certificación de ingresos por facturación

Genera, con el formato del estudio:

1. `CERTIFICACION_DE_INGRESOS_<APELLIDO>_<AAAA_MM>.docx` — Word editable (certificación + declaración).
2. `CERTIFICACION_DE_INGRESOS_<APELLIDO>_<AAAA_MM>.pdf` — certificación del contador (hojas 1-2).
3. `CERTIFICACION_DE_INGRESOS_<APELLIDO>_<AAAA_MM> - ANEXO.pdf` — declaración de ingresos firmada por el cliente + cierre "Firmado por mí a los efectos de su identificación…" con la firma del contador.

`<AAAA_MM>` = mes en que termina el período certificado.

Código: repo **privado** `cjg044-wq/cjg_cert_tradicional`. Aun siendo privado, no subir firmas, la fuente Tahoma ni datos de clientes.

## 0. Preparar el entorno

Como el repo es privado, primero agregarlo a la sesión con `add_repo` (owner `cjg044-wq`, repo `cjg_cert_tradicional`, access `read`) y clonarlo con el comando que devuelve. Después:

```bash
git clone --depth 1 https://github.com/cjg044-wq/cjg_cert_tradicional /tmp/cjg_cert_tradicional 2>/dev/null || git -C /tmp/cjg_cert_tradicional pull
S=/tmp/cjg_cert_tradicional/scripts
```

Si no hay forma de acceder al repo, avisar a Cristian (no reescribir los scripts de memoria).

Assets privados (no están en el repo) en la carpeta de skills de Cristian:
`G:\Mi unidad\Claude - Skills\cjg-cert-tradicional\`
- `firma_cjg.png` — firma del contador.
- `tahoma_bold.ttf` — Tahoma Bold (la negrita real, para que el PDF salga igual que en Word).

Traerlos con las herramientas del equipo (ver punto 1) a `/tmp/cjg_assets/` y después:

```bash
python3 -I $S/setup_fuentes.py /tmp/cjg_assets            # instala Tahoma normal (clon Wine) + negrita
```

Si falta `tahoma_bold.ttf`, pasá como segundo argumento cualquier certificación anterior en PDF hecha con Word (`setup_fuentes.py /tmp/cjg_assets cert_anterior.pdf`): la extrae, la deja en assets y conviene devolverla a la carpeta de skills. Si falta `firma_cjg.png`, extraerla de una certificación anterior firmada (`pdfimages -png cert.pdf /tmp/cjg_assets/x` y renombrar la imagen de la firma) y avisar.

## 1. Carpetas de origen y destino

Cristian indica **desde qué carpeta tomar la documentación base** y **en qué carpeta dejar lo generado** (rutas de su PC, ej. `G:\Mi unidad\Contador CJGarcia\Clientes\<CLIENTE>\FACTURAS`).

- Si no indicó el origen, preguntárselo (una sola pregunta, junto con lo que falte del punto 3).
- Si no indicó el destino, usar la subcarpeta `CERTIFICACION` dentro de la carpeta de origen (crearla) y decirlo.
- Acceso a su computadora con las herramientas `mcp__remote-devices__*` (cargarlas con ToolSearch si están diferidas):
  1. `get_device_info` → ver carpetas conectadas. Si origen, destino o la carpeta de assets no están conectadas, pedirlas **en un solo** `device_request_folder_access` (origen, destino y `G:\Mi unidad\Claude - Skills\cjg-cert-tradicional`).
  2. `device_list_dir` del origen (recursive si hace falta) y `device_stage_files` de: PDFs de facturas/notas de crédito, exportación de Mis Comprobantes (.xlsx/.csv), constancia de inscripción, foto/PDF de la firma del cliente, y los assets. Lo stageado queda en `/mnt/user-data/uploads/<carpeta>/…`.
  3. Al final, `device_commit_files` de los 3 entregables a la carpeta de destino.
- Si la computadora no está conectada o no responde: trabajar con los archivos adjuntos al chat y entregar con `SendUserFile`, avisando que no se pudieron guardar en la carpeta.

## 2. Leer los comprobantes

```bash
python3 -I $S/leer_comprobantes.py /tmp/cert/comprobantes.json <carpeta_o_archivos_stageados>
```

- Lee PDFs de ARCA (solo la hoja ORIGINAL) y/o la exportación de Mis Comprobantes. Deduplica por tipo+PV+número.
- Notas de crédito van en negativo.
- Revisar y **reportar** los `avisos` (ej. período con año mal tipeado → se corrige con el año de "Hasta"; receptor del exterior cargado como "Proveedor del Exterior").
- Controlar que no falten números en la secuencia de cada punto de venta; si faltan, preguntar si están anulados o falta el archivo.

## 3. Datos del cliente

Armar `/tmp/cert/cliente.json` (ver `ejemplo/cliente_ejemplo.json`):

| Campo | De dónde sale |
|---|---|
| `nombre` | Apellido y nombres, en tipo título ("Perez Juan Carlos") |
| `trat` | "Sr." / "Sra." |
| `cuit` | del comprobante / constancia, con guiones (20-20123456-3) |
| `dni` | de la constancia o DNI; si no hay, derivarlo del CUIT (dígitos 3 a 10, con puntos) y **avisar que hay que confirmarlo** |
| `domicilio`, `localidad` | encabezado (calle y número / "Localidad, Provincia de X") |
| `domicilio_real` | texto del punto 1: calle y número, barrio o "entre calles …", "Localidad X, Provincia de Y" |
| `actividad` | descripción de la actividad de ARCA, en MAYÚSCULAS |
| `columna` | título de la columna del cuadro mensual (ej. "Servicios Profesionales", "Servicios Personales") |
| `lugar_decl` | lugar de la declaración del cliente: su localidad |
| `fecha` | fecha de la certificación = **hoy** (dd/mm/aaaa) |
| `criterio_mes` | `"periodo"` (default) o `"emision"` — ver criterios |
| `firma_cliente` | PNG de la firma del cliente, si la hay |

**Actividad, domicilio y categoría**: consultar el CUIT en `https://consulta-cuit.eureka-asesoramiento.com/` con el navegador incorporado (rechazar cookies no esenciales → pegar el CUIT en "Ingrese CUITs" → Consultar → "Ver detalle de un CUIT"). De ahí: actividad principal, domicilio fiscal (incluye "entre calles"), localidad, provincia, situación IVA y categoría de monotributo. La constancia de `seti.afip.gob.ar` pide CAPTCHA: no resolverlo; si Cristian quiere usarla, cargar el CUIT y pedirle que complete el CAPTCHA.

Si quedan datos sin resolver, preguntarlos todos juntos; si Cristian no está, poner el mejor dato disponible y listarlo como pendiente.

**Firma del cliente** (foto o escaneo):
```bash
python3 -I $S/limpiar_firma.py foto_firma.jpg /tmp/cert/firma_cliente.png azul   # o "negra"
```
Recorta y saca el fondo. Sin firma, el anexo queda con la línea de firma, nombre y CUIT para firmar a mano.

## 4. Generar

```bash
python3 -I $S/armar_datos.py /tmp/cert/comprobantes.json /tmp/cert/cliente.json /tmp/cert/datos.json
PREVIEW_DIR=/tmp/cert/preview $S/generar.sh /tmp/cert/datos.json /mnt/user-data/outputs/cert_<APELLIDO> /tmp/cjg_assets
```

Los entregables van bajo `/mnt/user-data/outputs/` porque `device_commit_files` solo toma archivos de ahí. Mirar **todas** las imágenes de `/tmp/cert/preview` antes de entregar.

## Criterios (validados por Cristian)

- **Formato**: idéntico al modelo — Word en carta, Tahoma 10, márgenes sup. 2 cm / izq. 3 cm; el PDF se escala a A4 como lo imprimía PDFCreator. Cuadros con encabezado azul `#44546A`, letra Arial blanca negrita. Lista de documentación en cursiva.
- **Período certificado**:
  - `criterio_mes = "periodo"` (facturas de servicios con período facturado): desde el primer "Período Facturado Desde" hasta el último "Hasta"; cada factura se imputa al mes de su período (aunque se haya emitido después).
  - `criterio_mes = "emision"` (sin período facturado): meses completos desde el primer al último mes de emisión; se imputa por fecha de emisión.
  - Si el período lo define Cristian, cargar `desde`/`hasta` en cliente.json.
- **Total** = suma de facturas y notas de débito menos notas de crédito; en letras: "pesos … con NN centavos" (apócope correcta: "cincuenta y un millones", "veintiún mil").
- **Documentación respaldatoria** (punto 4): un renglón para facturas y otro para notas de crédito/débito, con rangos por punto de venta en formato `C-00006-00000001`.
- **Declaración (anexo)**: "<lugar_decl>, <fecha>" con la localidad del cliente; tabla Fecha / Tipo / Punto de Venta / Número Desde / Imp. Total; TOTAL al lado de la firma del cliente. Si no entra en una hoja, el bloque TOTAL + firma pasa entero a la hoja siguiente (nunca se parte).
- **Cierre del anexo**: "Firmado por mí a los efectos de su identificación con mi certificación de fecha DD/MM/AAAA" — misma fecha que la certificación.
- **Firma del contador**: Cristian Javier García, Contador Público, Universidad Nacional de Córdoba, Matrícula 10-21827-5 CPCE Córdoba. Lugar: "Ciudad de Córdoba, Provincia de Córdoba".
- **Formato argentino** en todo: fechas dd/mm/aaaa, importes 1.234.567,89.

## Controles antes de entregar

- Total de la certificación = total del cuadro mensual = TOTAL del anexo.
- Monto en letras bien escrito.
- Sin páginas en blanco; el bloque TOTAL + firma del anexo no se parte.
- **Monotributo**: comparar lo facturado con la categoría de ARCA (y los topes vigentes, buscándolos si hace falta). Si supera la categoría, avisar (recategorización / riesgo de exclusión).
- Reportar anomalías de los comprobantes (fechas o años mal cargados, condición IVA del receptor, números faltantes).

## Entrega

1. `device_commit_files` de los 3 archivos a la carpeta de destino (o `SendUserFile` si no hay conexión con la PC).
2. Respuesta breve: total certificado, período, dónde quedaron los archivos y **lista de datos pendientes de confirmar** (DNI derivado, domicilio, criterio de período, firma del cliente faltante, etc.).
