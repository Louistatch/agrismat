"""
Génération de rapports PDF professionnels pour Agri-Smart.
Utilise ReportLab pour produire un document multi-pages avec :
  - Page de garde avec logo, site, date
  - Résumé exécutif (KPIs)
  - Profil pédologique & climatique
  - Tableau des besoins en eau par culture
  - Bilan hydrique détaillé par culture
  - Graphiques (barres + Kc)
  - Footer avec sources et numérotation
"""
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus import Image as RLImage
from reportlab.graphics.shapes import Drawing, Rect, String, Line, PolyLine
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF
from reportlab.graphics.widgets.markers import makeMarker

# ── Palette ───────────────────────────────────────────────────────────────────
GREEN_DARK  = colors.HexColor("#166534")
GREEN_MID   = colors.HexColor("#16a34a")
GREEN_LIGHT = colors.HexColor("#dcfce7")
BLUE_DARK   = colors.HexColor("#1d4ed8")
BLUE_LIGHT  = colors.HexColor("#dbeafe")
AMBER       = colors.HexColor("#b45309")
AMBER_LIGHT = colors.HexColor("#fef3c7")
SLATE_900   = colors.HexColor("#0f172a")
SLATE_700   = colors.HexColor("#334155")
SLATE_500   = colors.HexColor("#64748b")
SLATE_300   = colors.HexColor("#cbd5e1")
SLATE_100   = colors.HexColor("#f1f5f9")
WHITE       = colors.white

CHART_COLORS = [
    colors.HexColor("#166534"), colors.HexColor("#16a34a"),
    colors.HexColor("#1d4ed8"), colors.HexColor("#b45309"),
    colors.HexColor("#7c3aed"), colors.HexColor("#0e7490"),
    colors.HexColor("#be185d"),
]

W, H = A4  # 595 x 842 pt
MARGIN = 2.0 * cm
CONTENT_W = W - 2 * MARGIN


# ── Styles ────────────────────────────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()
    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "cover_title": s("cover_title",
            fontSize=28, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_CENTER, leading=34),
        "cover_sub": s("cover_sub",
            fontSize=13, fontName="Helvetica",
            textColor=SLATE_300, alignment=TA_CENTER, leading=18),
        "cover_meta": s("cover_meta",
            fontSize=10, fontName="Helvetica",
            textColor=SLATE_300, alignment=TA_CENTER, leading=14),
        "section": s("section",
            fontSize=9, fontName="Helvetica-Bold",
            textColor=SLATE_900, spaceBefore=18, spaceAfter=6,
            textTransform="uppercase", letterSpacing=1.2),
        "body": s("body",
            fontSize=9, fontName="Helvetica",
            textColor=SLATE_700, leading=13),
        "small": s("small",
            fontSize=8, fontName="Helvetica",
            textColor=SLATE_500, leading=11),
        "kpi_val": s("kpi_val",
            fontSize=18, fontName="Helvetica-Bold",
            textColor=SLATE_900, alignment=TA_CENTER, leading=22),
        "kpi_lbl": s("kpi_lbl",
            fontSize=7.5, fontName="Helvetica-Bold",
            textColor=SLATE_500, alignment=TA_CENTER,
            textTransform="uppercase", letterSpacing=0.8),
        "kpi_sub": s("kpi_sub",
            fontSize=8, fontName="Helvetica",
            textColor=SLATE_500, alignment=TA_CENTER),
        "th": s("th",
            fontSize=8, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_CENTER),
        "td": s("td",
            fontSize=8, fontName="Helvetica",
            textColor=SLATE_700, alignment=TA_CENTER),
        "td_left": s("td_left",
            fontSize=8, fontName="Helvetica",
            textColor=SLATE_700, alignment=TA_LEFT),
        "td_total": s("td_total",
            fontSize=8, fontName="Helvetica-Bold",
            textColor=GREEN_DARK, alignment=TA_CENTER),
        "footer": s("footer",
            fontSize=7.5, fontName="Helvetica",
            textColor=SLATE_500, alignment=TA_CENTER),
        "chart_title": s("chart_title",
            fontSize=8.5, fontName="Helvetica-Bold",
            textColor=SLATE_700, spaceAfter=4),
    }


# ── Page template (header/footer) ─────────────────────────────────────────────
class _PageTemplate:
    def __init__(self, loc_display, date_str):
        self.loc = loc_display
        self.date = date_str

    def on_page(self, canvas, doc):
        canvas.saveState()
        # Top rule
        canvas.setStrokeColor(SLATE_300)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, H - 1.2*cm, W - MARGIN, H - 1.2*cm)
        # Header text
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(GREEN_DARK)
        canvas.drawString(MARGIN, H - 0.9*cm, "Agri-Smart")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(SLATE_500)
        canvas.drawString(MARGIN + 55, H - 0.9*cm, "· Irrigation Expert System")
        canvas.drawRightString(W - MARGIN, H - 0.9*cm, self.loc)
        # Bottom rule
        canvas.line(MARGIN, 1.4*cm, W - MARGIN, 1.4*cm)
        # Footer
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(SLATE_500)
        canvas.drawString(MARGIN, 0.9*cm,
            "NASA POWER Climatology · ROSETTA v3 USDA-ARS · FAO-56 Penman-Monteith")
        canvas.drawRightString(W - MARGIN, 0.9*cm,
            f"Page {doc.page}  ·  {self.date}")
        canvas.restoreState()

    def on_first_page(self, canvas, doc):
        pass  # cover page has its own layout


# ── Cover page ────────────────────────────────────────────────────────────────
def _cover_page(canvas, doc, loc_display, lat, lon, date_str, crops, system_name):
    canvas.saveState()
    # Dark background
    canvas.setFillColor(SLATE_900)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    # Green accent bar top
    canvas.setFillColor(GREEN_DARK)
    canvas.rect(0, H - 0.6*cm, W, 0.6*cm, fill=1, stroke=0)
    # Green accent bar bottom
    canvas.rect(0, 0, W, 0.4*cm, fill=1, stroke=0)

    # Logo mark
    cx, cy = W / 2, H * 0.72
    canvas.setFillColor(GREEN_DARK)
    canvas.roundRect(cx - 22, cy - 22, 44, 44, 6, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 22)
    canvas.drawCentredString(cx, cy - 8, "AS")

    # Title
    canvas.setFont("Helvetica-Bold", 30)
    canvas.setFillColor(WHITE)
    canvas.drawCentredString(W / 2, H * 0.60, "Agri-Smart")
    canvas.setFont("Helvetica", 13)
    canvas.setFillColor(SLATE_300)
    canvas.drawCentredString(W / 2, H * 0.55, "Rapport d'Irrigation · Expert System")

    # Divider
    canvas.setStrokeColor(GREEN_DARK)
    canvas.setLineWidth(1.5)
    canvas.line(W/2 - 60, H * 0.52, W/2 + 60, H * 0.52)

    # Site info box
    bx, by, bw, bh = MARGIN, H * 0.30, CONTENT_W, H * 0.19
    canvas.setFillColor(colors.HexColor("#1e293b"))
    canvas.roundRect(bx, by, bw, bh, 8, fill=1, stroke=0)
    canvas.setStrokeColor(GREEN_DARK)
    canvas.setLineWidth(1)
    canvas.roundRect(bx, by, bw, bh, 8, fill=0, stroke=1)

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(SLATE_300)
    canvas.drawString(bx + 16, by + bh - 20, "SITE")
    canvas.setFont("Helvetica-Bold", 14)
    canvas.setFillColor(WHITE)
    canvas.drawString(bx + 16, by + bh - 38, loc_display)

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(SLATE_500)
    canvas.drawString(bx + 16, by + bh - 54, f"Coordonnées : {lat:.4f}°N, {lon:.4f}°E")

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(SLATE_300)
    canvas.drawString(bx + 16, by + 38, "CULTURES ANALYSÉES")
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(WHITE)
    canvas.drawString(bx + 16, by + 22, "  ·  ".join(crops))

    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(SLATE_300)
    canvas.drawRightString(bx + bw - 16, by + 38, "SYSTÈME D'IRRIGATION")
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(WHITE)
    canvas.drawRightString(bx + bw - 16, by + 22, system_name)

    # Date
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(SLATE_500)
    canvas.drawCentredString(W / 2, H * 0.24, f"Généré le {date_str}")

    # Bottom note
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(SLATE_500)
    canvas.drawCentredString(W / 2, 0.8*cm,
        "NASA POWER Climatology · ROSETTA v3 USDA-ARS · FAO-56 Penman-Monteith")
    canvas.restoreState()


# ── Helpers ───────────────────────────────────────────────────────────────────
def _hr(story):
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=SLATE_300, spaceAfter=6, spaceBefore=2))

def _section(story, title, badge=None, ST=None):
    badge_txt = f"  [{badge}]" if badge else ""
    story.append(Paragraph(title + badge_txt, ST["section"]))
    _hr(story)

def _kpi_row(story, items, ST):
    """items = list of (label, value, sub, color)"""
    n = len(items)
    col_w = CONTENT_W / n
    cells = []
    for label, value, sub, color in items:
        cell = [
            Paragraph(label, ST["kpi_lbl"]),
            Spacer(1, 3),
            Paragraph(f'<font color="{color}">{value}</font>', ST["kpi_val"]),
            Spacer(1, 2),
            Paragraph(sub, ST["kpi_sub"]),
        ]
        cells.append(cell)

    t = Table([cells], colWidths=[col_w] * n)
    t.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 0.5, SLATE_300),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, SLATE_300),
        ("BACKGROUND", (0, 0), (-1, -1), SLATE_100),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))


def _data_table(story, headers, rows, col_widths, ST, total_row_idx=None):
    """Tableau générique avec header vert et lignes alternées."""
    th_cells = [Paragraph(h, ST["th"]) for h in headers]
    data = [th_cells]
    for ri, row in enumerate(rows):
        is_total = (total_row_idx is not None and ri == total_row_idx)
        style = ST["td_total"] if is_total else ST["td"]
        style_l = ST["td_total"] if is_total else ST["td_left"]
        cells = []
        for ci, val in enumerate(row):
            st_ = style_l if ci == 0 else style
            cells.append(Paragraph(str(val), st_))
        data.append(cells)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    ts = [
        ("BACKGROUND",    (0, 0), (-1, 0),  GREEN_DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  8),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",         (0, 1), (0, -1),  "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("GRID",          (0, 0), (-1, -1), 0.4, SLATE_300),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SLATE_100]),
    ]
    if total_row_idx is not None:
        tr = total_row_idx + 1
        ts += [
            ("BACKGROUND", (0, tr), (-1, tr), GREEN_LIGHT),
            ("FONTNAME",   (0, tr), (-1, tr), "Helvetica-Bold"),
            ("TEXTCOLOR",  (0, tr), (-1, tr), GREEN_DARK),
        ]
    t.setStyle(TableStyle(ts))
    story.append(t)
    story.append(Spacer(1, 10))


# ── Charts ────────────────────────────────────────────────────────────────────
def _bar_chart(all_dfs, MOIS, crop_colors):
    """Graphique barres groupées : besoins mensuels par culture."""
    dw, dh = CONTENT_W * 0.72, 5.5 * cm
    d = Drawing(dw, dh)

    bc = VerticalBarChart()
    bc.x, bc.y = 40, 20
    bc.width  = dw - 55
    bc.height = dh - 30

    crops = list(all_dfs.keys())
    bc.data = [
        [all_dfs[crop].loc[all_dfs[crop]["mois"] == m, "volume_ha"].values[0]
         for m in MOIS]
        for crop in crops
    ]
    bc.categoryAxis.categoryNames = [m[:3] for m in MOIS]
    bc.categoryAxis.labels.fontSize = 7
    bc.categoryAxis.labels.angle = 0
    bc.valueAxis.labels.fontSize = 7
    bc.valueAxis.valueMin = 0
    bc.groupSpacing = 4
    bc.barSpacing   = 1

    for i, crop in enumerate(crops):
        bc.bars[i].fillColor   = crop_colors[i % len(crop_colors)]
        bc.bars[i].strokeColor = None
        bc.bars[i].strokeWidth = 0

    bc.categoryAxis.strokeColor = SLATE_300
    bc.valueAxis.strokeColor    = SLATE_300
    bc.categoryAxis.gridStrokeColor = colors.transparent
    bc.valueAxis.gridStrokeColor    = SLATE_100

    d.add(bc)

    # Legend
    lx = 42
    for i, crop in enumerate(crops):
        d.add(Rect(lx, dh - 12, 8, 8,
                   fillColor=crop_colors[i % len(crop_colors)], strokeColor=None))
        d.add(String(lx + 11, dh - 11, crop,
                     fontSize=7, fillColor=SLATE_700))
        lx += len(crop) * 5.5 + 22

    return d


def _kc_chart(all_dfs, MOIS, KC_VALUES, crop_colors):
    """Graphique lignes : coefficients Kc par culture."""
    dw, dh = CONTENT_W * 0.72, 5.5 * cm
    d = Drawing(dw, dh)

    lp = LinePlot()
    lp.x, lp.y = 40, 20
    lp.width  = dw - 55
    lp.height = dh - 30

    crops = list(all_dfs.keys())
    xs = list(range(len(MOIS)))

    lp.data = [
        [(xs[i], KC_VALUES[crop]["kc"][i]) for i in range(len(MOIS))]
        for crop in crops
    ]

    for i, crop in enumerate(crops):
        lp.lines[i].strokeColor = crop_colors[i % len(crop_colors)]
        lp.lines[i].strokeWidth = 1.5
        lp.lines[i].symbol = makeMarker("Circle")
        lp.lines[i].symbol.size = 3
        lp.lines[i].symbol.fillColor = crop_colors[i % len(crop_colors)]

    lp.xValueAxis.valueMin  = 0
    lp.xValueAxis.valueMax  = len(MOIS) - 1
    lp.xValueAxis.valueStep = 1
    lp.xValueAxis.labelTextFormat = lambda v: MOIS[int(v)][:3] if 0 <= int(v) < len(MOIS) else ""
    lp.xValueAxis.labels.fontSize = 7
    lp.yValueAxis.valueMin  = 0
    lp.yValueAxis.valueMax  = 1.4
    lp.yValueAxis.valueStep = 0.2
    lp.yValueAxis.labels.fontSize = 7

    # Kc=1 reference line
    ref_y = lp.y + (1.0 / 1.4) * lp.height
    d.add(Line(lp.x, ref_y, lp.x + lp.width, ref_y,
               strokeColor=SLATE_300, strokeDashArray=[3, 3], strokeWidth=0.8))
    d.add(String(lp.x + lp.width + 2, ref_y - 3, "Kc=1",
                 fontSize=6.5, fillColor=SLATE_500))

    d.add(lp)

    # Legend
    lx = 42
    for i, crop in enumerate(crops):
        d.add(Rect(lx, dh - 12, 8, 8,
                   fillColor=crop_colors[i % len(crop_colors)], strokeColor=None))
        d.add(String(lx + 11, dh - 11, crop,
                     fontSize=7, fillColor=SLATE_700))
        lx += len(crop) * 5.5 + 22

    return d


# ── Main builder ──────────────────────────────────────────────────────────────
def generate_pdf(
    lat, lon, loc_display,
    soil_data, climate_data,
    selected_crops, crop_areas,
    all_dfs, system_name, eff,
    total_saison, mois_pic, vol_pic, debit_pompe,
    MOIS, JOURS_MOIS, KC_VALUES,
):
    """
    Génère le rapport PDF complet et retourne les bytes.
    Utilise BaseDocTemplate avec deux PageTemplate :
      - 'cover'   : page 1 pleine page, sans marges
      - 'content' : pages suivantes avec header/footer
    """
    from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate, Frame
    from reportlab.pdfgen import canvas as rl_canvas

    buf = BytesIO()
    date_str = datetime.now().strftime("%d/%m/%Y a %H:%M")

    # ── Document ──────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=1.8*cm, bottomMargin=1.8*cm,
        title="Agri-Smart · Rapport d'Irrigation",
        author="Agri-Smart Expert System",
        subject=f"Rapport irrigation · {loc_display}",
    )

    ST = _styles()
    pt = _PageTemplate(loc_display, date_str)

    # Closures pour les callbacks de page
    _cover_args = (loc_display, lat, lon, date_str, selected_crops, system_name)

    def on_cover(canvas, doc):
        _cover_page(canvas, doc, *_cover_args)

    def on_content(canvas, doc):
        pt.on_page(canvas, doc)

    # ── Frames ────────────────────────────────────────────────────────────────
    cover_frame = Frame(0, 0, W, H, leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0, id="cover")
    content_frame = Frame(MARGIN, 1.8*cm, CONTENT_W, H - 1.8*cm - 1.8*cm,
                          leftPadding=0, rightPadding=0,
                          topPadding=0, bottomPadding=0, id="normal")

    cover_tpl   = PageTemplate(id="Cover",   frames=[cover_frame],   onPage=on_cover)
    content_tpl = PageTemplate(id="Content", frames=[content_frame], onPage=on_content)

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        pageTemplates=[cover_tpl, content_tpl],
        title="Agri-Smart - Rapport d'Irrigation",
        author="Agri-Smart Expert System",
    )

    story = []

    # ── Page de garde (frame vide — tout dessiné par onPage) ──────────────────
    from reportlab.platypus.doctemplate import NextPageTemplate
    story.append(NextPageTemplate("Cover"))
    story.append(PageBreak())          # déclenche on_cover sur page 1

    # ── Basculer sur le template contenu ──────────────────────────────────────
    story.append(NextPageTemplate("Content"))

    # 1. Résumé exécutif ───────────────────────────────────────────────────────
    _section(story, "Resume Executif", ST=ST)

    total_ha = sum(crop_areas.values())
    _kpi_row(story, [
        ("Volume total saison",  f"{total_saison:,.0f} m3",
         f"{total_ha:.1f} ha - {system_name}", "#166534"),
        ("Mois de pointe",       mois_pic,
         f"{vol_pic:,.0f} m3 - pic de demande", "#b45309"),
        ("Debit pompe estime",   f"{debit_pompe:.2f} L/s",
         "Pompage 12 h/j - mois de pointe", "#1d4ed8"),
        ("Moyenne mensuelle",    f"{total_saison/12:,.0f} m3",
         f"Efficience {int(eff*100)}% - {system_name}", "#334155"),
    ], ST)

    # 2. Profil pédologique ────────────────────────────────────────────────────
    _section(story, "Profil Pedologique", badge=soil_data["source"], ST=ST)

    soil_rows = [[
        soil_data["texture"],
        f"{soil_data['clay_pct']}%",
        f"{soil_data['sand_pct']}%",
        f"{soil_data['silt_pct']}%",
        f"{soil_data['fc_pct']}%",
        f"{soil_data['wp_pct']}%",
        f"{soil_data['RU']} mm/m",
        f"{soil_data['RFU']} mm/m",
        f"{soil_data['bdod']} g/cm3",
    ]]
    cw = CONTENT_W / 9
    _data_table(story,
        ["Texture", "Argile", "Sable", "Limon", "FC", "WP", "RU", "RFU", "Da"],
        soil_rows, [cw]*9, ST)

    # 3. Données climatiques ───────────────────────────────────────────────────
    _section(story, "Donnees Climatiques", badge=climate_data["source"], ST=ST)

    _idx = [3,4,5,6,7,8,9,10,11,0,1,2]
    clim_headers = ["Parametre"] + [m[:3] for m in MOIS] + ["Annuel"]
    etp_row   = ["ETP (mm/j)"] + [
        str(round(climate_data["etp_mensuelle"][i], 1)) for i in _idx
    ] + [str(round(sum(climate_data["etp_mensuelle"])/12, 1))]
    pluie_row = ["Pluie (mm)"] + [
        str(round(climate_data["pluie_mensuelle"][i], 0)) for i in _idx
    ] + [str(round(sum(climate_data["pluie_mensuelle"]), 0))]
    temp_row  = ["Temp. (C)"] + [
        str(round(climate_data["temp_mensuelle"][i], 1)) for i in _idx
    ] + [str(climate_data["avg_temp"])]

    cw2 = [2.2*cm] + [((CONTENT_W - 2.2*cm) / 13)] * 13
    _data_table(story, clim_headers,
                [etp_row, pluie_row, temp_row], cw2, ST)

    # 4. Besoins en eau par culture ────────────────────────────────────────────
    story.append(PageBreak())
    _section(story, "Besoins en Eau par Culture",
             badge="m3/ha/mois - FAO-56", ST=ST)

    pivot_headers = ["Culture"] + [m[:3] for m in MOIS] + ["Total/ha", "Sup.(ha)", "Total(m3)"]
    pivot_rows = []
    for crop in selected_crops:
        df = all_dfs[crop]
        row = [crop]
        for m in MOIS:
            v = df.loc[df["mois"] == m, "volume_ha"].values
            row.append(f"{v[0]:.0f}" if len(v) else "0")
        row += [
            f"{df['volume_ha'].sum():.0f}",
            f"{crop_areas[crop]:.1f}",
            f"{df['volume_total'].sum():.0f}",
        ]
        pivot_rows.append(row)

    total_row = ["TOTAL"]
    for m in MOIS:
        total_row.append(
            f"{sum(all_dfs[c].loc[all_dfs[c]['mois']==m,'volume_ha'].values[0] for c in selected_crops):.0f}"
        )
    total_row += [
        f"{sum(all_dfs[c]['volume_ha'].mean() for c in selected_crops):.0f}",
        f"{sum(crop_areas.values()):.1f}",
        f"{total_saison:.0f}",
    ]
    pivot_rows.append(total_row)

    cw3 = [2.0*cm] + [((CONTENT_W - 2.0*cm - 3.5*cm) / 12)] * 12 + [1.3*cm, 1.1*cm, 1.1*cm]
    _data_table(story, pivot_headers, pivot_rows, cw3, ST,
                total_row_idx=len(pivot_rows)-1)

    # 5. Graphiques ────────────────────────────────────────────────────────────
    _section(story, "Analyse Visuelle", ST=ST)
    _charts_row(story, ST, all_dfs, MOIS, KC_VALUES)

    # 6. Bilan hydrique détaillé par culture ───────────────────────────────────
    for crop in selected_crops:
        story.append(PageBreak())
        _section(story, f"Bilan Hydrique - {crop}",
                 badge=f"{crop_areas[crop]} ha", ST=ST)

        df = all_dfs[crop]
        _kpi_row(story, [
            ("Volume total",   f"{df['volume_total'].sum():,.0f} m3",
             f"{crop_areas[crop]} ha", "#166534"),
            ("Besoin net max", f"{df['besoin_net'].max():.0f} mm",
             df.loc[df['besoin_net'].idxmax(), 'mois'], "#b45309"),
            ("Kc moyen",       f"{df['kc'].mean():.2f}",
             "Coefficient cultural FAO-56", "#1d4ed8"),
            ("ETP moyenne",    f"{df['etp'].mean():.2f} mm/j",
             "Penman-Monteith", "#334155"),
        ], ST)

        det_headers = [
            "Mois", "Jours", "ETP\n(mm/j)", "Kc", "Z\n(m)",
            "ETM\n(mm)", "Pluie\n(mm)", "Peff\n(mm)", "RFU\n(mm)",
            "Besoin\nnet", "Besoin\nbrut", "Vol.\nm3/ha", "Vol.\ntotal"
        ]
        det_rows = []
        for _, r in df.iterrows():
            det_rows.append([
                r["mois"][:3], int(r["nb_jours"]),
                f"{r['etp']:.2f}", f"{r['kc']:.2f}", f"{r['z']:.2f}",
                f"{r['etm']:.1f}", f"{r['pluie']:.1f}", f"{r['peff']:.1f}",
                f"{r['rfu']:.1f}", f"{r['besoin_net']:.1f}",
                f"{r['besoin_brut']:.1f}", f"{r['volume_ha']:.1f}",
                f"{r['volume_total']:.1f}",
            ])
        sums = df.sum(numeric_only=True)
        det_rows.append([
            "TOTAL", int(sums["nb_jours"]),
            f"{df['etp'].mean():.2f}", f"{df['kc'].mean():.2f}",
            f"{df['z'].mean():.2f}", f"{sums['etm']:.1f}",
            f"{sums['pluie']:.1f}", f"{sums['peff']:.1f}",
            f"{sums['rfu']:.1f}", f"{sums['besoin_net']:.1f}",
            f"{sums['besoin_brut']:.1f}", f"{sums['volume_ha']:.1f}",
            f"{sums['volume_total']:.1f}",
        ])

        cw4 = [1.3*cm, 0.9*cm] + [(CONTENT_W - 2.2*cm) / 11] * 11
        _data_table(story, det_headers, det_rows, cw4, ST,
                    total_row_idx=len(det_rows)-1)

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story)
    return buf.getvalue()


def _charts_row(story, ST, all_dfs, MOIS, KC_VALUES):
    """Insère les deux graphiques côte à côte."""
    chart_w = CONTENT_W / 2 - 4

    bar_title = Paragraph("Besoins mensuels par culture (m3/ha)", ST["chart_title"])
    kc_title  = Paragraph("Coefficients culturaux Kc - FAO-56",   ST["chart_title"])
    bar_d = _bar_chart(all_dfs, MOIS, CHART_COLORS)
    kc_d  = _kc_chart(all_dfs, MOIS, KC_VALUES, CHART_COLORS)

    t = Table(
        [[bar_title, kc_title], [bar_d, kc_d]],
        colWidths=[chart_w, chart_w],
    )
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))
