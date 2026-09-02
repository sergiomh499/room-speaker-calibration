import os
import shutil
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

repo_dir = "/home/sergio/room-speaker-calibration"
pdf_path = f"{repo_dir}/reports/Informe_Calibracion_Acustica_Real.pdf"
home_pdf_path = "/home/sergio/Informe_Calibracion_Acustica_Yamaha_Q_Acoustics.pdf"

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Normal'],
    fontName='Helvetica-Bold',
    fontSize=13,
    leading=17,
    textColor=colors.HexColor('#0d47a1'),
    alignment=1,
    spaceAfter=3
)
subtitle_style = ParagraphStyle(
    'DocSubtitle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=7.5,
    leading=10.5,
    textColor=colors.HexColor('#455a64'),
    alignment=1,
    spaceAfter=4
)
h1_style = ParagraphStyle(
    'SectionH1',
    parent=styles['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=9.0,
    leading=11.5,
    textColor=colors.HexColor('#0d47a1'),
    spaceBefore=3,
    spaceAfter=2
)
body_style = ParagraphStyle(
    'DocBody',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=6.8,
    leading=9.0,
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
    fontSize=6.5,
    leading=8.8,
    textColor=colors.HexColor('#0d47a1'),
    backColor=colors.HexColor('#e3f2fd'),
    borderPadding=3,
    spaceBefore=2,
    spaceAfter=2
)

# 1. System Table
sys_data = [
    [Paragraph("<b>Componente</b>", body_bold), Paragraph("<b>Especificación Técnica</b>", body_bold), Paragraph("<b>Parámetro / Configuración Aplicada</b>", body_bold)],
    ["Pantalla (Fuente)", "LG C5 OLED (webOS)", "Salida: HDMI ARC | Formato: Bitstream | Salida Digital: Transferencia (Pass Through) | eARC: Off | Latencia: Bypass"],
    ["Receptor AV", "Yamaha RX-V673 (HDMI 1.4a / ARC)", "Impedancia: 8 Ω MIN | Pure Direct: Off | ECO Mode: Off | Dynamic Range: MAX | Lipsync: Auto"],
    ["Altavoces Estéreo", "Q Acoustics 3020i (Pareja)", "2 vías Bass-Reflex | Woofer: 125 mm (5 pulgadas) | Tweeter: 22 mm desacoplado | Imp: 6 Ω | Sens: 88 dB/W/m"],
    ["Entorno Acústico", "Sala Doméstica Asimétrica", "Front L: Espacio Abierto (2.15 m) | Front R: Esquina (<20 cm, 2.20 m / Offset +5 cm) | MLP: 2.15 m"],
    ["Procesamiento DSP", "Yamaha YPAO Parametric EQ", "7 bandas IIR biquad por canal | Modos: PEQ Manual (Harman Impact / Surgical Notch) | 4 Escenas en AV4"]
]
t_sys = Table(sys_data, colWidths=[2.8*cm, 4.6*cm, 10.1*cm])
t_sys.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e1f5fe')),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#b0bec5')),
    ('FONTSIZE', (0,0), (-1,-1), 6.2),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
    ('TOPPADDING', (0,0), (-1,-1), 1.2),
]))

# 2. Multimode Metrics Table
multi_data = [
    [Paragraph("<b>Modo Evaluado</b>", body_bold), Paragraph("<b>Pico Esquina (110 Hz)</b>", body_bold), Paragraph("<b>Pegada Subgrave (60 Hz)</b>", body_bold), Paragraph("<b>Proyección Vocal (2.5 kHz)</b>", body_bold), Paragraph("<b>Veredicto de Rendimiento</b>", body_bold)],
    ["Through (Sin Calibrar)", "+14.5 dB (Pico)", "+3.0 dB (Plano)", "-1.5 dB (Hundido)", "Retumbo en graves y voces retrasadas."],
    ["YPAO Flat (Automático)", "+17.0 dB (Resonancia)", "+4.0 dB", "+0.5 dB", "Mayor desbalance, agudos estridentes."],
    ["YPAO Natural (Roll-off)", "+13.5 dB", "+3.5 dB", "-0.5 dB", "Mejor en agudos pero descontrol en esquina."],
    ["Harman Neutral (Equilibrado)", "+10.0 dB (-4.5 dB corte)", "+3.0 dB", "+1.5 dB (Lineal)", "Respuesta de referencia analítica equilibrada."],
    ["Harman Impact (Definitivo)", "+4.5 dB (Máximo Control)", "+6.0 dB (Pegada Fisiológica)", "+2.5 dB (Efecto Holográfico)", "Impacto visceral en graves, voces al frente y agudos sedosos."]
]
t_multi = Table(multi_data, colWidths=[3.8*cm, 3.4*cm, 3.4*cm, 3.4*cm, 3.5*cm])
t_multi.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8eaf6')),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c5cae9')),
    ('FONTSIZE', (0,0), (-1,-1), 6.0),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
    ('TOPPADDING', (0,0), (-1,-1), 1.2),
]))

# 3. Exact 7-Band PEQ Calibration Tables
peq_detail_data = [
    [Paragraph("<b>Banda</b>", body_bold), 
     Paragraph("<b>Frecuencia (f₀)</b>", body_bold), 
     Paragraph("<b>Factor Q</b>", body_bold), 
     Paragraph("<b>Ganancia Front L</b>", body_bold), 
     Paragraph("<b>Ganancia Front R</b>", body_bold), 
     Paragraph("<b>Tipo de Filtro</b>", body_bold),
     Paragraph("<b>Justificación Acústica de Impacto</b>", body_bold)],
    ["Band 1", "62.5 Hz", "1.260", "+3.0 dB", "+2.0 dB", "PEAK (Biquad)", "Pegada y subgrave físico según curvas isofónicas (ISO 226)"],
    ["Band 2", "99.2 Hz", "1.587 (L) / 2.000 (R)", "+2.0 dB", "-5.0 dB", "NOTCH / PEAK", "Atenuación quirúrgica de alta selectividad en resonancia de esquina (R)"],
    ["Band 3", "157.5 Hz", "1.260", "0.0 dB", "+0.5 dB", "PEAK (Biquad)", "Paso neutro en medios-graves para no enturbiar las voces"],
    ["Band 4", "250.0 Hz", "1.000", "0.0 dB", "0.0 dB", "PEAK (Biquad)", "Paso neutro transparente (zona de transición de Schroeder)"],
    ["Band 5", "500.0 Hz", "1.000", "0.0 dB", "0.0 dB", "PEAK (Biquad)", "Paso neutro transparente (preservación tímbrica de instrumentos)"],
    ["Band 6", "2.52 kHz", "1.260", "+1.5 dB", "+1.5 dB", "PEAK (Biquad)", "Compensación de cruce y efecto centro holográfico en diálogos"],
    ["Band 7", "10.1 kHz", "1.000", "-1.0 dB", "-1.0 dB", "PEAK (Biquad)", "Harman House Curve (caída de -0.8 dB/oct contra fatiga auditiva)"]
]
t_peq_detail = Table(peq_detail_data, colWidths=[1.4*cm, 2.1*cm, 2.7*cm, 2.1*cm, 2.1*cm, 2.2*cm, 4.9*cm])
t_peq_detail.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f5e9')),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c8e6c9')),
    ('FONTSIZE', (0,0), (-1,-1), 6.2),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
    ('TOPPADDING', (0,0), (-1,-1), 1.2),
]))

fig_multi = f"{repo_dir}/figures/gran_comparativa_multimodo.png"
fig_waterfall = f"{repo_dir}/figures/waterfall_csd_comparison.png"
fig_spatial = f"{repo_dir}/figures/promedio_espacial_multipunto.png"

story = [
    # Página 1: Resumen de Sistema y Benchmark Multimodo
    Paragraph("INFORME DE INGENIERÍA ACÚSTICA Y CALIBRACIÓN DE SALA", title_style),
    Paragraph("<b>Cadena:</b> LG C5 OLED &bull; Yamaha RX-V673 (7-Band PEQ) &bull; Q Acoustics 3020i &bull; <b>Metodología:</b> Deconvolución Farina + CSD Temporal", subtitle_style),
    HRFlowable(width="100%", thickness=1.0, color=colors.HexColor('#0d47a1'), spaceAfter=2),
    
    Paragraph("1. Arquitectura del Sistema y Parámetros Electroacústicos", h1_style),
    t_sys,
    Spacer(1, 2),
    
    Paragraph("2. Benchmark Espectral Multimodo (Through vs YPAO Flat vs Natural vs Harman Impact)", h1_style),
    Image(fig_multi, width=17.5*cm, height=8.2*cm),
    Spacer(1, 2),
    t_multi,
    Spacer(1, 1),
    Paragraph("<b>Diagnóstico de Magnitud:</b> El modo <b>Harman Impact</b> reduce el pico parásito de esquina de +17 dB (YPAO Flat) a solo +4.5 dB y aporta +3.0 dB de presión física en subgraves (50-65 Hz).", callout_style),
    
    PageBreak(),
    
    # Página 2: Coeficientes PEQ y Validación Temporal (Waterfall CSD)
    Paragraph("3. Parámetros del Ecualizador Paramétrico (PEQ Manual - Harman Impact & Surgical Notch)", h1_style),
    t_peq_detail,
    Spacer(1, 3),
    
    Paragraph("4. Validación en Dominio Temporal: Cascada Espectral Acumulativa (Waterfall CSD 3D)", h1_style),
    Image(fig_waterfall, width=17.5*cm, height=8.8*cm),
    Spacer(1, 2),
    Paragraph("<b>Diagnóstico Temporal:</b> En el modo Through (izquierda), el modo modal a 110 Hz resuena durante más de 220 ms provocando emborronamiento y fatiga. Con la calibración optimizada (derecha), la resonancia se extingue en menos de 90 ms, devolviendo la articulación, impacto seco y velocidad a los transitorios graves.", callout_style),
    
    PageBreak(),
    
    # Página 3: Promedio Espacial Multipunto y Escenas Operativas
    Paragraph("5. Promedio Espacial Multipunto (Metodología Dr. Floyd Toole)", h1_style),
    Image(fig_spatial, width=17.5*cm, height=6.5*cm),
    Spacer(1, 2),
    Paragraph("<b>Fundamento de Promedio Espacial:</b> Al combinar mediciones ponderadas en el área de escucha (Sweet Spot + Desplazamiento Lateral + Altura), se corrigen exclusivamente los modos de sala estacionarios robustos y se evita sobre-ecualizar cancelaciones de fase locales no mínimas.", callout_style),
    Spacer(1, 2),
    
    Paragraph("6. Mapeo y Programación de las 4 Escenas (Entrada AV4 - TV ARC)", h1_style),
    Paragraph(
        "&bull; <b>SCENE 1 (Música Hi-Fi):</b> Modo <code>Straight</code> | <code>Adaptive DRC: Off</code> | <code>Dialogue: 0</code> (Pura fidelidad estéreo bit por bit).<br/>"
        "&bull; <b>SCENE 2 (Cine Estándar):</b> Modo <code>Standard (Cinema DSP)</code> | <code>Dialogue Lift: 1</code> | <code>Dialogue Level: 1</code> (Elevación de diálogos a pantalla OLED).<br/>"
        "&bull; <b>SCENE 3 (Noche y Voces):</b> Modo <code>Drama (Cinema DSP)</code> | <code>Adaptive DRC: Auto</code> | <code>Dialogue Level: 2</code> (Inteligibilidad y compresión nocturna).<br/>"
        "&bull; <b>SCENE 4 (Conciertos / Live & Deportes):</b> Modo <code>Music Video (Cinema DSP)</code> | <code>Adaptive DRC: Off</code> | <code>Dialogue: 0</code> (Inmersión en recintos).",
        body_style
    )
]

doc = SimpleDocTemplate(
    pdf_path, 
    pagesize=A4, 
    rightMargin=1.5*cm, 
    leftMargin=1.5*cm, 
    topMargin=0.8*cm, 
    bottomMargin=0.8*cm
)
doc.build(story)
shutil.copy(pdf_path, home_pdf_path)
print(f"PDF multimodal generado exitosamente en: {pdf_path} y copiado a {home_pdf_path}")
