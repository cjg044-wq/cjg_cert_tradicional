import sys, pypdf
from pypdf import Transformation, PageObject
src, dst = sys.argv[1], sys.argv[2]
r = pypdf.PdfReader(src); w = pypdf.PdfWriter()
A4W, A4H = 595.276, 841.89
for pg in r.pages:
    pw, ph = float(pg.mediabox.width), float(pg.mediabox.height)
    s = min(A4W/pw, A4H/ph)
    tx, ty = (A4W - pw*s)/2, (A4H - ph*s)/2
    new = PageObject.create_blank_page(width=A4W, height=A4H)
    new.merge_transformed_page(pg, Transformation().scale(s, s).translate(tx, ty))
    w.add_page(new)
w.write(dst)
