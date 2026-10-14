# -*- coding: utf-8 -*-
"""
Convierte informe.md en un PDF con formato APA 7.ª edición (trabajo de estudiante).

Uso:
    python generar_pdf_apa.py                      # informe.md -> Informe_APA.pdf
    python generar_pdf_apa.py otro.md salida.pdf

Qué aplica del formato APA:
  - Portada de estudiante (título, autores, institución, curso, docente, fecha) tomada
    del bloque inicial entre líneas '---' de informe.md.
  - Hoja carta, márgenes de 2,54 cm, número de página arriba a la derecha.
  - Times New Roman 12 pt, doble espacio, sangría de 1,27 cm en la primera línea.
  - Encabezados: # nivel 1 (centrado, negrita), ## nivel 2 (izquierda, negrita),
    ### nivel 3 (izquierda, negrita cursiva).
  - Tablas: «Tabla N» en negrita, título en cursiva, solo líneas horizontales, nota debajo.
  - Figuras: «Figura N» en negrita, título en cursiva, imagen, nota debajo.
  - Resumen sin sangría; «Referencias» y apéndices en página nueva; referencias con
    sangría francesa.

Convenciones del Markdown (todas se ven bien también en GitHub):
  **Tabla 1**                    -> rótulo de tabla
  *Título de la tabla*           -> título (párrafo siguiente al rótulo)
  | tabla en formato GitHub |
  *Nota.* Texto de la nota.      -> nota de tabla o figura
  ![texto](resultados/fig.png)   -> imagen (en un párrafo propio)
  <!-- salto -->                 -> salto de página en el PDF

Requisitos: pip install reportlab markdown-it-py pillow
"""
import os
import re
import sys
from xml.sax.saxutils import escape

from markdown_it import MarkdownIt
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

BASE = os.path.dirname(os.path.abspath(__file__))
ENTRADA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "informe.md")
SALIDA = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "Informe_APA.pdf")
DIR_MD = os.path.dirname(os.path.abspath(ENTRADA))

# ---------------------------------------------------------------------------
# Fuente: Times New Roman (Windows / macOS) o Liberation Serif (Linux, mismas métricas)
# ---------------------------------------------------------------------------
CANDIDATAS = [
    ("C:/Windows/Fonts/times.ttf", "C:/Windows/Fonts/timesbd.ttf",
     "C:/Windows/Fonts/timesi.ttf", "C:/Windows/Fonts/timesbi.ttf"),
    ("/System/Library/Fonts/Supplemental/Times New Roman.ttf",
     "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
     "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf",
     "/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf"),
    ("/Library/Fonts/Times New Roman.ttf", "/Library/Fonts/Times New Roman Bold.ttf",
     "/Library/Fonts/Times New Roman Italic.ttf", "/Library/Fonts/Times New Roman Bold Italic.ttf"),
    ("/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf",
     "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf",
     "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Italic.ttf",
     "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold_Italic.ttf"),
    ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"),
]
FUENTE = None
for rutas in CANDIDATAS:
    if all(os.path.exists(r) for r in rutas):
        for nombre, ruta in zip(("APA", "APA-B", "APA-I", "APA-BI"), rutas):
            pdfmetrics.registerFont(TTFont(nombre, ruta))
        registerFontFamily("APA", normal="APA", bold="APA-B", italic="APA-I", boldItalic="APA-BI")
        FUENTE = "APA"
        break
if FUENTE is None:
    print("Aviso: no se encontró Times New Roman ni Liberation Serif; se usa Times-Roman integrada "
          "(los símbolos griegos como χ o λ pueden no verse).")
    FUENTE = "Times-Roman"
    registerFontFamily("Times-Roman", normal="Times-Roman", bold="Times-Bold",
                       italic="Times-Italic", boldItalic="Times-BoldItalic")
MONO = "Courier"

# ---------------------------------------------------------------------------
# Estilos APA
# ---------------------------------------------------------------------------
PT, DOBLE, SANGRIA = 12, 24, 1.27 * cm
MARGEN = 2.54 * cm
ANCHO_TEXTO = letter[0] - 2 * MARGEN

E = {
    "cuerpo": ParagraphStyle("cuerpo", fontName=FUENTE, fontSize=PT, leading=DOBLE,
                             firstLineIndent=SANGRIA, alignment=TA_LEFT),
    "sin_sangria": ParagraphStyle("sin_sangria", fontName=FUENTE, fontSize=PT, leading=DOBLE),
    "h1": ParagraphStyle("h1", fontName=FUENTE, fontSize=PT, leading=DOBLE, alignment=TA_CENTER,
                         keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName=FUENTE, fontSize=PT, leading=DOBLE, keepWithNext=1),
    "h3": ParagraphStyle("h3", fontName=FUENTE, fontSize=PT, leading=DOBLE, keepWithNext=1),
    "rotulo": ParagraphStyle("rotulo", fontName=FUENTE, fontSize=PT, leading=DOBLE, keepWithNext=1),
    "titulo_obj": ParagraphStyle("titulo_obj", fontName=FUENTE, fontSize=PT, leading=DOBLE, keepWithNext=1),
    "nota": ParagraphStyle("nota", fontName=FUENTE, fontSize=PT, leading=DOBLE, spaceBefore=4),
    "ref": ParagraphStyle("ref", fontName=FUENTE, fontSize=PT, leading=DOBLE,
                          leftIndent=SANGRIA, firstLineIndent=-SANGRIA),
    "lista": ParagraphStyle("lista", fontName=FUENTE, fontSize=PT, leading=DOBLE,
                            leftIndent=SANGRIA + 0.5 * cm, bulletIndent=SANGRIA),
    "celda": ParagraphStyle("celda", fontName=FUENTE, fontSize=10, leading=12.5),
    "codigo": ParagraphStyle("codigo", fontName=MONO, fontSize=8, leading=11, leftIndent=0.6 * cm,
                             spaceBefore=4, spaceAfter=10),
    "portada": ParagraphStyle("portada", fontName=FUENTE, fontSize=PT, leading=DOBLE, alignment=TA_CENTER),
}


def con_alineacion(estilo, al):
    a = {"center": TA_CENTER, "left": TA_LEFT}.get(al, TA_LEFT)
    return ParagraphStyle(estilo.name + al, parent=estilo, alignment=a)


# ---------------------------------------------------------------------------
# Lectura del Markdown
# ---------------------------------------------------------------------------
texto = open(ENTRADA, encoding="utf-8").read()
meta = {}
m = re.match(r"^---\s*\n(.*?)\n---\s*\n", texto, re.S)
if m:
    for linea in m.group(1).splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    texto = texto[m.end():]

md = MarkdownIt("commonmark", {"html": True}).enable("table")
tokens = md.parse(texto)

ETIQUETAS_OK = {"sup", "/sup", "sub", "/sub", "br", "br/", "br /", "b", "/b", "i", "/i"}


def inline_a_xml(tok):
    """Convierte un token inline de markdown-it al mini-HTML de ReportLab."""
    out = []
    for c in tok.children or []:
        t = c.type
        if t == "text":
            out.append(escape(c.content))
        elif t == "strong_open":
            out.append("<b>")
        elif t == "strong_close":
            out.append("</b>")
        elif t == "em_open":
            out.append("<i>")
        elif t == "em_close":
            out.append("</i>")
        elif t == "code_inline":
            out.append(f"<font face='{MONO}' size='{PT - 1.5}'>{escape(c.content)}</font>")
        elif t == "softbreak":
            out.append(" ")
        elif t == "hardbreak":
            out.append("<br/>")
        elif t == "html_inline":
            etiqueta = c.content.strip("<>").strip().lower()
            if etiqueta in ETIQUETAS_OK:
                out.append("<br/>" if etiqueta.startswith("br") else c.content.lower())
        elif t in ("link_open", "link_close", "image"):
            pass
        else:
            out.append(escape(c.content or ""))
    return "".join(out)


def imagen_de(tok):
    hijos = [c for c in (tok.children or []) if not (c.type == "text" and not c.content.strip())]
    if len(hijos) == 1 and hijos[0].type == "image":
        return hijos[0].attrs.get("src")
    return None


def flowable_imagen(src):
    ruta = os.path.join(DIR_MD, src)
    if not os.path.exists(ruta):
        return Paragraph(f"[Falta la imagen: {escape(src)}. Ejecute primero analisis_factorial.py]", E["sin_sangria"])
    w, h = PILImage.open(ruta).size
    ancho = ANCHO_TEXTO
    alto = ancho * h / w
    max_alto = 17 * cm
    if alto > max_alto:
        alto, ancho = max_alto, max_alto * w / h
    img = Image(ruta, width=ancho, height=alto)
    img.hAlign = "CENTER"
    return img


def flowable_tabla(filas, alineaciones):
    ncol = len(filas[0])
    # Ancho de columnas: ancho natural del contenido; si no cabe, se encogen solo las
    # columnas de texto largo (que pueden partirse en varias líneas).
    est = E["celda"]
    plano = lambda c: re.sub(r"<[^>]+>", "", c).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    natural, minimo = [], []
    for j in range(ncol):
        textos = [plano(filas[i][j]) for i in range(len(filas))]
        natural.append(max(pdfmetrics.stringWidth(t, est.fontName, est.fontSize) for t in textos) + 10)
        # celdas cortas (p. ej. «Se retiene») no se parten; las largas se parten por palabras
        palabras = [t if len(t) <= 14 else w for t in textos for w in (t.split() or [""])] or [""]
        minimo.append(max(pdfmetrics.stringWidth(w, est.fontName, est.fontSize) for w in palabras) + 10)
    if sum(natural) <= ANCHO_TEXTO:
        extra = (ANCHO_TEXTO - sum(natural)) / ncol
        anchos = [n + extra for n in natural]
    else:
        holgura = sum(natural) - sum(minimo)
        disponible = max(ANCHO_TEXTO - sum(minimo), 0)
        razon = disponible / holgura if holgura > 0 else 0
        anchos = [mi + (na - mi) * razon for mi, na in zip(minimo, natural)]
    datos = []
    for i, fila in enumerate(filas):
        celdas = []
        for j, c in enumerate(fila):
            al = "center" if i == 0 else (alineaciones[j] or ("left" if j == 0 else "center"))
            celdas.append(Paragraph(c, con_alineacion(E["celda"], al)))
        datos.append(celdas)
    t = Table(datos, colWidths=anchos, repeatRows=1, hAlign="CENTER")
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.9, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.9, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


# ---------------------------------------------------------------------------
# Recorrido de bloques -> lista de (tipo, flowable)
# ---------------------------------------------------------------------------
items = []
seccion = ""
primer_parrafo_resumen = True
anterior = None
i = 0
while i < len(tokens):
    tk = tokens[i]
    t = tk.type
    if t == "heading_open":
        nivel = int(tk.tag[1])
        contenido = inline_a_xml(tokens[i + 1])
        plano = tokens[i + 1].content.strip()
        if nivel == 1:
            seccion = plano
            if (plano == "Referencias" or plano.startswith("Apéndice") or plano.startswith("Anexo")) \
                    and items and items[-1][0] != "salto":
                items.append(("salto", PageBreak()))
            items.append(("h", Paragraph(f"<b>{contenido}</b>", E["h1"])))
        elif nivel == 2:
            items.append(("h", Paragraph(f"<b>{contenido}</b>", E["h2"])))
        else:
            items.append(("h", Paragraph(f"<b><i>{contenido}</i></b>", E["h3"])))
        anterior = "h"
        i += 3
        continue
    if t == "paragraph_open":
        inl = tokens[i + 1]
        crudo = inl.content.strip()
        src = imagen_de(inl)
        xml = inline_a_xml(inl)
        if src:
            items.append(("imagen", flowable_imagen(src)))
            anterior = "imagen"
        elif re.match(r"^\*\*(Tabla|Figura)\s+[A-Z]?\d+\*\*$", crudo):
            items.append(("rotulo", Paragraph(xml, E["rotulo"])))
            anterior = "rotulo"
        elif anterior == "rotulo":
            items.append(("titulo", Paragraph(xml, E["titulo_obj"])))
            anterior = "titulo"
        elif crudo.startswith("*Nota.*"):
            items.append(("nota", Paragraph(xml, E["nota"])))
            anterior = "nota"
        elif seccion == "Referencias":
            items.append(("p", Paragraph(xml, E["ref"])))
            anterior = "p"
        elif seccion == "Resumen" and primer_parrafo_resumen:
            items.append(("p", Paragraph(xml, E["sin_sangria"])))
            primer_parrafo_resumen = False
            anterior = "p"
        else:
            items.append(("p", Paragraph(xml, E["cuerpo"])))
            anterior = "p"
        i += 3
        continue
    if t in ("bullet_list_open", "ordered_list_open"):
        ordenada = t == "ordered_list_open"
        n = int(tk.attrs.get("start", 1)) if ordenada else 1
        nivel_lista = 1
        i += 1
        while i < len(tokens) and nivel_lista > 0:
            if tokens[i].type in ("bullet_list_open", "ordered_list_open"):
                nivel_lista += 1
            elif tokens[i].type in ("bullet_list_close", "ordered_list_close"):
                nivel_lista -= 1
            elif tokens[i].type == "inline":
                viñeta = f"{n}." if ordenada else "•"
                items.append(("p", Paragraph(inline_a_xml(tokens[i]), E["lista"], bulletText=viñeta)))
                n += 1
            i += 1
        anterior = "p"
        continue
    if t == "table_open":
        filas, alineaciones, fila = [], [], None
        i += 1
        while tokens[i].type != "table_close":
            x = tokens[i]
            if x.type == "tr_open":
                fila = []
            elif x.type in ("th_open", "td_open"):
                estilo = x.attrs.get("style", "") or ""
                if x.type == "th_open":
                    alineaciones.append("center" if "center" in estilo else ("left" if "left" in estilo else None))
            elif x.type == "inline":
                fila.append(inline_a_xml(x))
            elif x.type == "tr_close":
                filas.append(fila)
            i += 1
        items.append(("tabla", flowable_tabla(filas, alineaciones)))
        anterior = "tabla"
        i += 1
        continue
    if t in ("fence", "code_block"):
        items.append(("codigo", Preformatted(tk.content.rstrip("\n"), E["codigo"])))
        anterior = "codigo"
        i += 1
        continue
    if t == "html_block":
        if tk.content.strip().lower() == "<!-- salto -->":
            items.append(("salto", PageBreak()))
        i += 1
        continue
    i += 1

# Agrupar rótulo + título + tabla/imagen + nota para que no se separen entre páginas
historia = []
k = 0
while k < len(items):
    tipo, fl = items[k]
    if tipo == "rotulo":
        grupo = [fl]
        k += 1
        while k < len(items) and items[k][0] in ("titulo", "tabla", "imagen"):
            grupo.append(items[k][1])
            k += 1
        if k < len(items) and items[k][0] == "nota":
            grupo.append(items[k][1])
            k += 1
        grupo.append(Spacer(1, 10))
        alto_tabla = sum(1 for g in grupo if isinstance(g, Table) and len(g._cellvalues) > 22)
        historia.extend(grupo if alto_tabla else [KeepTogether(grupo)])
        continue
    historia.append(fl)
    k += 1

# ---------------------------------------------------------------------------
# Portada de estudiante (APA 7)
# ---------------------------------------------------------------------------
portada = [Spacer(1, 5.5 * cm),
           Paragraph(f"<b>{escape(meta.get('titulo', 'Título del trabajo'))}</b>", E["portada"]),
           Spacer(1, DOBLE)]
for clave in ("autores", "institucion", "curso", "docente", "fecha"):
    if meta.get(clave):
        portada.append(Paragraph(escape(meta[clave]), E["portada"]))
portada.append(PageBreak())


def numero_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont(FUENTE, PT)
    canvas.drawRightString(letter[0] - MARGEN, letter[1] - 1.27 * cm - PT * 0.3, str(doc.page))
    canvas.restoreState()


doc = SimpleDocTemplate(SALIDA, pagesize=letter, leftMargin=MARGEN, rightMargin=MARGEN,
                        topMargin=MARGEN, bottomMargin=MARGEN,
                        title=meta.get("titulo", ""), author=meta.get("autores", ""))
doc.build(portada + historia, onFirstPage=numero_pagina, onLaterPages=numero_pagina)
print(f"PDF generado: {SALIDA}")
