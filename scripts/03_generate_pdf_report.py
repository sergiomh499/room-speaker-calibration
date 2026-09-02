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
    fontSize=14,
    leading=18,
    textColor=colors.HexColor('#0d47a1'),
    alignment=1,
    spaceAfter=3
)
subtitle_style = ParagraphStyle(
    'DocSubtitle',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=8.0,
    leading=11,
    textColor=colors.HexColor('#455a64'),
    alignment=1,
    spaceAfter=5
)
h1_style = ParagraphStyle(
    'SectionH1',
    parent=styles['Heading1'],
    fontName='Helvetica-Bold',
    fontSize=10.0,
    leading=13,
    textColor=colors.HexColor('#0d47a1'),
    spaceBefore=4,
    spaceAfter=2
)
body_style = ParagraphStyle(
    'DocBody',
    parent=styles['Normal'],
    fontName='Helvetica',
    fontSize=7.2,
    leading=10.0,
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
    fontSize=7.0,
    leading=9.5,
    textColor=colors.HexColor('#0d47a1'),
    backColor=colors.HexColor('#e3f2fd'),
    borderPadding=3,
    spaceBefore=2,
    spaceAfter=3
)

# 1. System Table
sys_data = [
    [Paragraph("<b>Componente</b>", body_bold), Paragraph("<b>Especificación Técnica</b>", body_bold), Paragraph("<b>Parámetro / Configuración Aplicada</b>", body_bold)],
    ["Pantalla (Fuente)", "LG C5 OLED (webOS)", "Salida: HDMI ARC | Formato: Bitstream | Salida Digital: Transferencia (Pass Through) | eARC: Off | Latencia: Bypass"],
    ["Receptor AV", "Yamaha RX-V673 (HDMI 1.4a / ARC)", "Impedancia: 8 Ω MIN | Pure Direct: Off | ECO Mode: Off | Dynamic Range: MAX | Lipsync: Auto"],
    ["Altavoces Estéreo", "Q Acoustics 3020i (Pareja)", "2 vías Bass-Reflex | Woofer: 125 mm (5 pulgadas) | Tweeter: 22 mm desacoplado | Imp: 6 Ω | Sens: 88 dB/W/m"],
    ["Entorno Acústico", "Sala Doméstica Asimétrica", "Front L: Espacio Abierto (>50 cm) | Front R: Esquina (<20 cm, Corner-loading) | MLP: 2.1 m"],
    ["Procesamiento DSP", "Yamaha YPAO Parametric EQ", "7 bandas IIR biquad por canal | Modos: PEQ Manual (Harman Neutral) | 4 Escenas Programadas en AV4"]
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

# 2. Multimode Metrics Table
multi_data = [
    [Paragraph("<b>Modo Evaluado</b>", body_bold), Paragraph("<b>Desbalance Estéreo (|L-R|)</b>", body_bold), Paragraph("<b>Pico en Esquina (110 Hz)</b>", body_bold), Paragraph("<b>Respuesta en Agudos (>8 kHz)</b>", body_bold), Paragraph("<b>Veredicto de Rendimiento</b>", body_bold)],
    ["Through (Sin Calibrar)", "1.27 dB", "+14.5 dB (Resonancia severa)", "+4.5 dB (Brillo excesivo)", "Retumbo en graves y fatiga auditiva."],
    ["YPAO Flat (Automático)", "1.78 dB", "+15.0 dB (Sin atenuar)", "+3.5 dB (Plano forzado)", "Mayor desbalance estéreo y dureza en agudos."],
    ["YPAO Natural (Roll-off)", "1.46 dB", "+13.5 dB (Sin atenuar)", "+2.0 dB (Roll-off leve)", "Mejor que Flat, pero no contiene la esquina."],
    ["Harman Neutral (Manual Pro)", "1.23 dB (Óptimo)", "+10.0 dB (-5.0 dB atenuado)", "Caída natural suave (-0.8 dB/oct)", "Máxima simetría estéreo, graves secos y cero fatiga."]
]
t_multi = Table(multi_data, colWidths=[3.5*cm, 3.2*cm, 3.4*cm, 3.4*cm, 4.0*cm])
t_multi.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8eaf6')),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c5cae9')),
    ('FONTSIZE', (0,0), (-1,-1), 6.5),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ('TOPPADDING', (0,0), (-1,-1), 1.5),
]))

# 3. Exact 7-Band PEQ Calibration Tables
peq_detail_data = [
    [Paragraph("<b>Banda</b>", body_bold), 
     Paragraph("<b>Frecuencia (f₀)</b>", body_bold), 
     Paragraph("<b>Factor Q</b>", body_bold), 
     Paragraph("<b>Ganancia Front L</b>", body_bold), 
     Paragraph("<b>Ganancia Front R</b>", body_bold), 
     Paragraph("<b>Tipo de Filtro</b>", body_bold),
     Paragraph("<b>Justificación Electroacústica</b>", body_bold)],
    ["Band 1", "62.5 Hz", "1.260", "+3.0 dB", "+1.5 dB", "PEAK (Biquad)", "Relleno y extensión controlada de subgraves"],
    ["Band 2", "99.2 Hz", "1.587 (L) / 1.260 (R)", "+3.0 dB", "-4.5 dB", "PEAK (Biquad)", "Atenúa la resonancia axial de esquina en R (-4.5 dB)"],
    ["Band 3", "157.5 Hz", "1.260", "0.0 dB", "+0.5 dB", "PEAK (Biquad)", "Paso neutro en medios-graves"],
    ["Band 4", "250.0 Hz", "1.000", "0.0 dB", "0.0 dB", "PEAK (Biquad)", "Paso neutro transparente (zona de transición de Schroeder)"],
    ["Band 5", "500.0 Hz", "1.000", "0.0 dB", "0.0 dB", "PEAK (Biquad)", "Paso neutro transparente (preservación tímbrica directa)"],
    ["Band 6", "2.52 kHz", "1.260", "+1.5 dB", "+1.5 dB", "PEAK (Biquad)", "Compensación del escalón anecoico del filtro divisor (3020i)"],
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

fig_multi = f"{repo_dir}/figures/gran_comparativa_multimodo.png"

story = [
    Paragraph("INFORME ACÚSTICO COMPARATIVO MULTIMODO Y CALIBRACIÓN DE SALA", title_style),
    Paragraph("<b>Cadena de Audio:</b> LG C5 OLED &bull; Yamaha RX-V673 (DSP 7-Band PEQ) &bull; Q Acoustics 3020i<br/><b>Metodología:</b> Deconvolución de Farina (Log-Sweep 15 Hz - 22 kHz, 65k FFT, Suavizado 1/24 Octava)", subtitle_style),
    HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#0d47a1'), spaceAfter=3),
    
    Paragraph("1. Arquitectura del Sistema y Parámetros Eléctricos", h1_style),
    t_sys,
    Spacer(1, 3),
    
    Paragraph("2. Gran Comparativa Acústica Multimodo (Through vs YPAO Flat vs Natural vs Harman)", h1_style),
    Image(fig_multi, width=17.5*cm, height=9.0*cm),
    Spacer(1, 2),
    t_multi,
    Spacer(1, 2),
    Paragraph("<b>Diagnóstico de la Comparativa:</b> La calibración manual híbrida (Harman Neutral) es la única que logra atenuar -5.0 dB en la resonancia de esquina (110 Hz), reduciendo el desbalance estéreo a 1.23 dB y aplicando la caída natural Harman en agudos frente a la elevación fatigante de YPAO Flat.", callout_style),
    
    PageBreak(),
    
    Paragraph("3. Coeficientes Numéricos del Ecualizador Paramétrico (Yamaha PEQ Manual)", h1_style),
    t_peq_detail,
    Spacer(1, 4),
    
    Paragraph("4. Mapeo y Programación de las 4 Escenas (Yamaha RX-V673)", h1_style),
    Paragraph(
        "<b>Entrada HDMI ARC:</b> Asignada a <b>AV4</b> para todo el flujo de audio de la LG C5 OLED.<br/>"
        "&bull; <b>SCENE 1 (Música Hi-Fi):</b> Modo <code>Straight</code> | <code>Adaptive DRC: Off</code> | <code>Dialogue: 0</code> (Pura fidelidad estéreo bit por bit).<br/>"
        "&bull; <b>SCENE 2 (Cine Estándar):</b> Modo <code>Standard (Cinema DSP)</code> | <code>Adaptive DRC: Off / MAX</code> | <code>Dialogue Level: +1</code>.<br/>"
        "&bull; <b>SCENE 3 (Noche y Voces):</b> Modo <code>Drama (Cinema DSP)</code> | <code>Adaptive DRC: Auto</code> | <code>Dialogue Level: +2</code> (Inteligibilidad vocal y nivelación nocturna).<br/>"
        "&bull; <b>SCENE 4 (Conciertos/Live & Deportes):</b> Modo <code>Music Video (Cinema DSP)</code> | <code>Adaptive DRC: Off</code> | <code>Dialogue: 0</code> (Inmersión de estadio/recinto).",
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
print(f"PDF multimodal generado exitosamente en: {pdf_path} y copiado a {home_pdf_path}")
