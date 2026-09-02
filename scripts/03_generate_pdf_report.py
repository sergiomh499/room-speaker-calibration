import os
import shutil
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

repo_dir = "/home/sergio/yamaha-qacoustics-calibration"
pdf_path = f"{repo_dir}/reports/Informe_Calibracion_Acustica_Real.pdf"
home_pdf_path = "/home/sergio/Informe_Calibracion_Acustica_Yamaha_Q_Acoustics.pdf"

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=15,
    leading=19,
    textColor=colors.HexColor('#0d47a1'),
    alignment=1,
    spaceAfter=3
)
subtitle_style = ParagraphStyle(
    'DocSubtitle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=8.5,
    leading=12,
    textColor=colors.HexColor('#455a64'),
    alignment=1,
    spaceAfter=6
)
h1_style = ParagraphStyle(
    'SectionH1',
    parent=styles['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=10.5,
    leading=14,
    textColor=colors.HexColor('#0d47a1'),
    spaceBefore=5,
    spaceAfter=3
)
body_style = ParagraphStyle(
    'DocBody',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=7.5,
    leading=10.5,
    textColor=colors.HexColor('#212121')
)
body_bold = ParagraphStyle(
    'DocBodyBold',
    parent=body_style,
    fontName='Helvetica-Bold'
)
callout_style = ParagraphStyle(
    'DocCallout',
    parent=styles['Normal'],
    fontName='Helvetica-Oblique',
    fontSize=7.5,
    leading=10,
    textColor=colors.HexColor('#0d47a1'),
    backColor=colors.HexColor('#e3f2fd'),
    borderPadding=4,
    spaceBefore=2,
    spaceAfter=3
)

# 1. System Table
sys_data = [
    [Paragraph("<b>Componente</b>", body_bold), Paragraph("<b>Especificación Técnica</b>", body_bold), Paragraph("<b>Parámetro / Configuración Aplicada</b>", body_bold)],
    ["Pantalla (Fuente)", "LG C5 OLED (webOS)", "Salida: HDMI ARC (Dispositivo HDMI) | Salida Digital: Transferencia (Pass Through) | eARC: Off | Entrada: Bitstream"],
    ["Receptor AV", "Yamaha RX-V673 (HDMI 1.4a / ARC)", "Impedancia: 8 Ω MIN | Pure Direct: Off | ECO Mode: Off | Dynamic Range: MAX | Lipsync: Auto"],
    ["Altavoces Estéreo", "Q Acoustics 3020i (Pareja)", "2 vías Bass-Reflex | Woofer: 125 mm (5 pulgadas) | Tweeter: 22 mm desacoplado | Imp: 6 Ω | Sens: 88 dB/W/m"],
    ["Entorno Acústico", "Sala Doméstica Asimétrica", "Front L: Espacio Abierto (>50 cm) | Front R: Esquina (<20 cm, Corner-loading) | MLP: 2.1 m (Triángulo Equilátero)"],
    ["Procesamiento DSP", "Yamaha YPAO Parametric EQ", "7 bandas IIR biquad por canal | Modos: PEQ Manual (Híbrido) | Scene 1: Straight | Scene 2: Cinema Standard"]
]
t_sys = Table(sys_data, colWidths=[3.0*cm, 4.8*cm, 9.7*cm])
t_sys.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e1f5fe')),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#b0bec5')),
    ('FONTSIZE', (0,0), (-1,-1), 6.5),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ('TOPPADDING', (0,0), (-1,-1), 1.5),
]))

# 2. Exact 7-Band PEQ Calibration Tables
peq_detail_data = [
    [Paragraph("<b>Banda</b>", body_bold), 
     Paragraph("<b>Frecuencia (f₀)</b>", body_bold), 
     Paragraph("<b>Factor Q</b>", body_bold), 
     Paragraph("<b>Ganancia Front L</b>", body_bold), 
     Paragraph("<b>Ganancia Front R</b>", body_bold), 
     Paragraph("<b>Tipo de Filtro</b>", body_bold),
     Paragraph("<b>Justificación Electroacústica</b>", body_bold)],
    ["Band 1", "62.5 Hz", "1.260", "-1.0 dB", "-1.5 dB", "PEAK (Biquad)", "Atenúa la ganancia de límite por proximidad de esquina/muro"],
    ["Band 2", "99.2 Hz", "1.587 (L) / 1.260 (R)", "-1.5 dB", "-1.5 dB", "PEAK (Biquad)", "Suprime el primer modo resonante axial de la sala alargada"],
    ["Band 3", "157.5 Hz", "1.260 (L) / 1.000 (R)", "-1.0 dB", "0.0 dB", "PEAK (Biquad)", "Limpia el retumbo en la octava baja de la voz masculina"],
    ["Band 4", "250.0 Hz", "1.000", "0.0 dB", "0.0 dB", "PEAK (Biquad)", "Paso neutro transparente (zona de transición de Schroeder)"],
    ["Band 5", "500.0 Hz", "1.000", "0.0 dB", "0.0 dB", "PEAK (Biquad)", "Paso neutro transparente (preservación tímbrica directa)"],
    ["Band 6", "2.52 kHz", "1.260", "+1.5 dB", "+1.5 dB", "PEAK (Biquad)", "Compensación del escalón anecoico del filtro divisor (Spinorama)"],
    ["Band 7", "10.1 kHz", "1.000", "-1.0 dB", "-1.0 dB", "PEAK (Biquad)", "Implementación de la curva de caída natural (Harman House Curve)"]
]
t_peq_detail = Table(peq_detail_data, colWidths=[1.4*cm, 2.1*cm, 2.6*cm, 2.1*cm, 2.1*cm, 2.2*cm, 5.0*cm])
t_peq_detail.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f5e9')),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c8e6c9')),
    ('FONTSIZE', (0,0), (-1,-1), 6.5),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ('TOPPADDING', (0,0), (-1,-1), 1.5),
]))

fig_real = f"{repo_dir}/figures/respuesta_acustica_real.png"
fig_ir = f"{repo_dir}/figures/respuesta_impulso_real.png"

story = [
    Paragraph("INFORME DE MEDICIÓN ACÚSTICA REAL Y CALIBRACIÓN DE SALA", title_style),
    Paragraph("<b>Cadena:</b> LG C5 OLED &bull; Yamaha RX-V673 (DSP PEQ Manual) &bull; Q Acoustics 3020i<br/><b>Metodología:</b> Deconvolución de Farina (Sine-Sweep 15 Hz - 22 kHz, 65k FFT, Suavizado 1/24 Octava)", subtitle_style),
    HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#0d47a1'), spaceAfter=4),
    
    Paragraph("1. Arquitectura del Sistema y Parámetros Eléctricos", h1_style),
    t_sys,
    Spacer(1, 4),
    
    Paragraph("2. Respuesta en Frecuencia y Simetría Estéreo Real (Medición Directa)", h1_style),
    Image(fig_real, width=17.5*cm, height=9.0*cm),
    Spacer(1, 2),
    Paragraph("<b>Diagnóstico de la Medición Real:</b> La gráfica muestra la respuesta no procesada (Raw FFT 65k) y la curva suavizada a 1/24 de octava. Se observa la asimetría modal natural de la sala (refuerzo de esquina en 110-250 Hz en Front R) y la alineación estéreo simétrica en medios y agudos con la caída natural <i>Harman House Curve</i> por encima de 8 kHz.", callout_style),
    
    PageBreak(),
    
    Paragraph("3. Respuesta al Impulso Medida (Deconvolución Temporal)", h1_style),
    Image(fig_ir, width=17.5*cm, height=6.0*cm),
    Spacer(1, 4),
    
    Paragraph("4. Coeficientes Numéricos del Ecualizador Paramétrico (Yamaha PEQ Manual)", h1_style),
    t_peq_detail,
    Spacer(1, 5),
    
    Paragraph("5. Configuración Operativa y Mapeo de Escenas", h1_style),
    Paragraph(
        "<b>Entrada Principal:</b> Asignada a <b>AV4 (HDMI ARC)</b>.<br/>"
        "&bull; <b>SCENE 1 (Música / Audición Pura):</b> Entrada <code>AV4</code> | Modo <code>Straight</code> | <code>Adaptive DRC: Off</code> | <code>Enhancer: Off</code> | <code>Dialogue Level: 0 (Inactivo por Straight)</code>.<br/>"
        "&bull; <b>SCENE 2 (Cine / Series / YouTube):</b> Entrada <code>AV4</code> | Modo <code>Standard (Cinema DSP)</code> | <code>Adaptive DRC: Auto</code> | <code>Dialogue Level: +1</code>.<br/>"
        "&bull; <b>Recomendación Física de Graves:</b> Ambos altavoces operan como <i>Bass-Reflex</i> abierto para máxima dinámica, controlando las resonancias con el ecualizador PEQ activo.",
        body_style
    )
]

doc = SimpleDocTemplate(
    pdf_path, 
    pagesize=A4, 
    rightMargin=1.5*cm, 
    leftMargin=1.5*cm, 
    topMargin=1.0*cm, 
    bottomMargin=1.0*cm
)
doc.build(story)
shutil.copy(pdf_path, home_pdf_path)
print(f"PDF generado exitosamente en: {pdf_path} y copiado a {home_pdf_path}")
