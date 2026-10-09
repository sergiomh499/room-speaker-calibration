import { TargetProfile } from "../types";

export const DEFAULT_TARGET_PROFILES: TargetProfile[] = [
  {
    "id": "harman_wide_room",
    "name": "Harman Target / Floyd Toole (Referencia Acústica Universal)",
    "category": "Música Hi-Fi",
    "badge": "🥇 #1 Estándar de Oro (AES / Dr. Floyd Toole / Sean Olive)",
    "description": "Compensa la ganancia acústica de sala manteniendo el balance tímbrico natural de los Q Acoustics 3020i. Aplica un notch quirúrgico de alto factor Q en los modos estacionarios bajo 400 Hz y corrige el dip de cruce del altavoz en 2.52 kHz (+1.5 dB) para máxima presencia.",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Graves secos, rápidos y articulados sin retumbos molestos.",
      "Timbre vocal natural y transparente sin fatiga auditiva.",
      "Excelente definición del escenario sonoro estéreo.",
      "Equilibrio perfecto para cualquier género musical moderno y clásico."
    ],
    "cons": [
      "Para fanáticos de los graves hipertrofiados en cine de acción puede sentirse comedido."
    ],
    "bands": {
      "Band 1": {
        "freq": 198.4,
        "q": 3.175,
        "gain": -6.0,
        "q_l": 3.175,
        "q_r": 3.175,
        "gain_l": -6.0,
        "gain_r": -6.0,
        "desc": "Modo modal compartido (198.4 Hz)"
      },
      "Band 2": {
        "freq": 125.0,
        "q": 3.175,
        "gain": -5.0,
        "q_l": 3.175,
        "q_r": 3.175,
        "gain_l": -5.0,
        "gain_r": 0.0,
        "desc": "Modo modal Front L (125.0 Hz) con pase neutro en R"
      },
      "Band 3": {
        "freq": 157.5,
        "q": 3.175,
        "gain": -3.0,
        "q_l": 3.175,
        "q_r": 3.175,
        "gain_l": -3.0,
        "gain_r": 0.0,
        "desc": "Modo modal Front L (157.5 Hz) con pase neutro en R"
      },
      "Band 4": {
        "freq": 2520.0,
        "q": 1.26,
        "gain": 1.5,
        "q_l": 1.26,
        "q_r": 1.26,
        "gain_l": 1.5,
        "gain_r": 1.5,
        "desc": "Compensación de cruce y directividad del altavoz (2520.0 Hz)"
      },
      "Band 5": {
        "freq": 500.0,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (500.0 Hz)"
      },
      "Band 6": {
        "freq": 630.0,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (630.0 Hz)"
      },
      "Band 7": {
        "freq": 793.7,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (793.7 Hz)"
      }
    },
    "sub_bands": {},
    "supported_topologies": [
      "2.0",
      "2.1"
    ],
    "sub_supported": true
  },
  {
    "id": "harman_bass_boost",
    "name": "Harman In-Room Bass+ (+4 dB Punch / Música Urbana & Electrónica)",
    "category": "Especiales & Gaming",
    "badge": "💥 Punch Bass+ (+4 dB Extra / Electrónica & Música Urbana)",
    "description": "Añade un shelf de graves de +4.0 dB por debajo de 105 Hz con transición suave hacia los medios. Extrae todo el potencial dinámico del transductor de graves de los 3020i sin provocar distorsión ni compresión térmica.",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Graves profundos, pesados y viscerales que parecen salir de altavoces de suelo.",
      "Pegada contundente en el bombo y líneas de bajo sintéticas.",
      "Conserva la neutralidad y claridad vocal en la banda media.",
      "Da vida a habitaciones grandes donde los graves tienden a dispersarse."
    ],
    "cons": [
      "A volúmenes extremos (+85 dB SPL) puede acercarse al límite mecánico del woofer de 5\"."
    ],
    "bands": {
      "Band 1": {
        "freq": 396.9,
        "q_l": 1.587,
        "q_r": 1.587,
        "gain_l": -3.5,
        "gain_r": -4.0,
        "desc": "Filtro optimizado 396.9 Hz (common_mode)"
      },
      "Band 2": {
        "freq": 198.4,
        "q_l": 3.175,
        "q_r": 3.175,
        "gain_l": -2.0,
        "gain_r": -2.0,
        "desc": "Filtro optimizado 198.4 Hz (common_mode)"
      },
      "Band 3": {
        "freq": 315.0,
        "q_l": 1.26,
        "q_r": 1.26,
        "gain_l": -3.0,
        "gain_r": 0.0,
        "desc": "Filtro optimizado 315.0 Hz (asym_mode)"
      },
      "Band 4": {
        "freq": 250.0,
        "q_l": 3.175,
        "q_r": 3.175,
        "gain_l": 0.0,
        "gain_r": -5.0,
        "desc": "Filtro optimizado 250.0 Hz (transparent_pass)"
      },
      "Band 5": {
        "freq": 500.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Filtro optimizado 500.0 Hz (inactive)"
      },
      "Band 6": {
        "freq": 630.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Filtro optimizado 630.0 Hz (inactive)"
      },
      "Band 7": {
        "freq": 793.7,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Filtro optimizado 793.7 Hz (inactive)"
      }
    },
    "sub_bands": {},
    "supported_topologies": [
      "2.0",
      "2.1"
    ],
    "sub_supported": true
  },
  {
    "id": "bk_1974",
    "name": "B&K 1974 (Calidez Analógica Británica / Cero Fatiga)",
    "category": "Música Hi-Fi",
    "badge": "🥈 #2 Leyenda Analógica (Brüel & Kjær 1974 House Curve)",
    "description": "Aplica una pendiente constante de caída de -0.9 dB por octava a partir de 400 Hz combinada con un toque cálido en graves (+3.0 dB <100 Hz). Neutraliza la aspereza de grabaciones digitales brillantes.",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Cero fatiga auditiva en sesiones maratonianas de varias horas.",
      "Sonido aterciopelado, corpóreo y muy musical.",
      "Graves redondos y confortables que llenan la sala.",
      "Ideal para masterizaciones modernas comprimidas o excesivamente brillantes."
    ],
    "cons": [
      "Pierde algo de 'aire' y micro-detalle extremo por encima de 10 kHz."
    ],
    "bands": {
      "Band 1": {
        "freq": 125.0,
        "q": 3.175,
        "gain": -5.0,
        "q_l": 3.175,
        "q_r": 3.175,
        "gain_l": -5.0,
        "gain_r": 0.0,
        "desc": "Modo modal Front L (125.0 Hz) con pase neutro en R"
      },
      "Band 2": {
        "freq": 2520.0,
        "q": 1.26,
        "gain": 1.5,
        "q_l": 1.26,
        "q_r": 1.26,
        "gain_l": 1.5,
        "gain_r": 1.5,
        "desc": "Compensación de cruce y directividad del altavoz (2520.0 Hz)"
      },
      "Band 3": {
        "freq": 10080.0,
        "q": 1.0,
        "gain": -1.5,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": -1.5,
        "gain_r": -1.5,
        "desc": "Compensación de cruce y directividad del altavoz (10080.0 Hz)"
      },
      "Band 4": {
        "freq": 31.3,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (31.3 Hz)"
      },
      "Band 5": {
        "freq": 500.0,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (500.0 Hz)"
      },
      "Band 6": {
        "freq": 630.0,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (630.0 Hz)"
      },
      "Band 7": {
        "freq": 793.7,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (793.7 Hz)"
      }
    },
    "sub_bands": {},
    "supported_topologies": [
      "2.0",
      "2.1"
    ],
    "sub_supported": true
  },
  {
    "id": "dirac_live",
    "name": "Dirac Live Modern Stereo (Dinámica y Separación Instrumental)",
    "category": "Audiófilo",
    "badge": "Dirac Studio Ready",
    "description": "Alineación inspirada en los algoritmos de Dirac Live: respuesta lineal con suave pendiente de sala (-0.6 dB/octava) y estante de graves controlado para máxima pegada transitoria y microdinámica.",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Claridad de imagen estéreo milimétrica y localización espacial.",
      "Pegada limpia y articulada en graves.",
      "Gran sensación de dinámica en música acústica y electrónica."
    ],
    "cons": [
      "Revela imperfecciones en mezclas musicales de baja calidad."
    ],
    "bands": {
      "Band 1": {
        "freq": 78.7,
        "q": 2.52,
        "gain": 0.0,
        "q_l": 2.52,
        "q_r": 2.52,
        "gain_l": 0.0,
        "gain_r": -2.0,
        "desc": "Ajuste en Bajos (78.7 Hz)"
      },
      "Band 2": {
        "freq": 396.9,
        "q": 1.587,
        "gain": -3.0,
        "q_l": 1.587,
        "q_r": 1.587,
        "gain_l": -3.0,
        "gain_r": -3.0,
        "desc": "Ajuste en Bajos (396.9 Hz)"
      },
      "Band 3": {
        "freq": 198.4,
        "q": 3.175,
        "gain": -2.0,
        "q_l": 3.175,
        "q_r": 3.175,
        "gain_l": -2.0,
        "gain_r": -2.0,
        "desc": "Ajuste en Bajos (198.4 Hz)"
      },
      "Band 4": {
        "freq": 2520.0,
        "q": 1.26,
        "gain": 1.0,
        "q_l": 1.26,
        "q_r": 1.26,
        "gain_l": 1.0,
        "gain_r": 1.0,
        "desc": "Ajuste en Medios (2520.0 Hz)"
      },
      "Band 5": {
        "freq": 10080.0,
        "q": 1.0,
        "gain": -0.5,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": -0.5,
        "gain_r": -0.5,
        "desc": "Ajuste en Altos (10080.0 Hz)"
      },
      "Band 6": {
        "freq": 12700.0,
        "q": 1.0,
        "gain": 2.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 2.0,
        "gain_r": 2.0,
        "desc": "Ajuste en Altos (12700.0 Hz)"
      },
      "Band 7": {
        "freq": 4000.0,
        "q": 1.26,
        "gain": -3.0,
        "q_l": 1.26,
        "q_r": 1.26,
        "gain_l": -3.0,
        "gain_r": -3.0,
        "desc": "Ajuste en Medios (4000.0 Hz)"
      }
    },
    "sub_bands": {},
    "supported_topologies": [
      "2.0",
      "2.1"
    ],
    "sub_supported": true
  },
  {
    "id": "cinema_blockbuster",
    "name": "Cinema Reference & THX (Inmersión Cinemática & Efectos LFE)",
    "category": "Cine",
    "badge": "Cine Reference THX",
    "description": "Curva de referencia para cine en casa inspirada en estándares THX y salas de postproducción. Realza el canal LFE y los efectos de sonido envolvente manteniendo los diálogos cristalinos.",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Impacto cinematográfico realista en explosiones y bandas sonoras orquestales.",
      "Diálogos nítidos y perfectamente inteligibles.",
      "Atenúa la estridencia de bandas sonoras a alto volumen."
    ],
    "cons": [
      "Graves contundentes que requieren moderación en horarios nocturnos."
    ],
    "bands": {
      "Band 1": {
        "freq": 2520.0,
        "q": 1.26,
        "gain": 2.0,
        "q_l": 1.26,
        "q_r": 1.26,
        "gain_l": 2.0,
        "gain_r": 2.0,
        "desc": "Compensación de cruce y directividad del altavoz (2520.0 Hz)"
      },
      "Band 2": {
        "freq": 10080.0,
        "q": 1.0,
        "gain": -1.5,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": -1.5,
        "gain_r": -1.5,
        "desc": "Compensación de cruce y directividad del altavoz (10080.0 Hz)"
      },
      "Band 3": {
        "freq": 31.3,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (31.3 Hz)"
      },
      "Band 4": {
        "freq": 39.4,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (39.4 Hz)"
      },
      "Band 5": {
        "freq": 500.0,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (500.0 Hz)"
      },
      "Band 6": {
        "freq": 630.0,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (630.0 Hz)"
      },
      "Band 7": {
        "freq": 793.7,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (793.7 Hz)"
      }
    },
    "sub_bands": {},
    "supported_topologies": [
      "2.0",
      "2.1"
    ],
    "sub_supported": true
  },
  {
    "id": "vocal_clarity",
    "name": "Vocal Clarity & Dialogue Enhanced (Claridad Vocal para Series & Cine)",
    "category": "Cine",
    "badge": "Dialogue Pro",
    "description": "Diseñado específicamente para series de TV, podcasts, noticias y películas donde los diálogos quedan enterrados por la música o los efectos. Atenúa las resonancias graves que enturbian las voces y aporta presencia a los formantes vocales.",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Inteligibilidad de diálogo perfecta incluso a volumen moderado o bajo.",
      "Elimina el efecto de voz encajonada o retumbante.",
      "Reduce la fatiga al escuchar series o podcasts largos."
    ],
    "cons": [
      "Menos impacto de subgraves en escenas de acción intensa."
    ],
    "bands": {
      "Band 1": {
        "freq": 78.7,
        "q": 1.587,
        "gain": -1.5,
        "desc": "Supresión de resonancia modal en graves (78.7 Hz)",
        "gain_l": -1.5,
        "gain_r": -1.5,
        "q_l": 1.587,
        "q_r": 1.587
      },
      "Band 2": {
        "freq": 198.4,
        "q": 3.175,
        "gain": -2.0,
        "desc": "Supresión modal de límite de sala (198.4 Hz)",
        "gain_l": -2.0,
        "gain_r": -2.0,
        "q_l": 3.175,
        "q_r": 3.175
      },
      "Band 3": {
        "freq": 396.9,
        "q": 1.587,
        "gain": -3.5,
        "desc": "Atenuación de retumbo para máxima articulación (396.9 Hz)",
        "gain_l": -3.5,
        "gain_r": -3.5,
        "q_l": 1.587,
        "q_r": 1.587
      },
      "Band 4": {
        "freq": 2520.0,
        "q": 1.26,
        "gain": 2.5,
        "desc": "Realce de inteligibilidad vocal humana (2520.0 Hz)",
        "gain_l": 2.5,
        "gain_r": 2.5,
        "q_l": 1.26,
        "q_r": 1.26
      },
      "Band 5": {
        "freq": 5000.0,
        "q": 1.5,
        "gain": 1.0,
        "desc": "Definición de consonantes sibilantes suaves (5000.0 Hz)",
        "gain_l": 1.0,
        "gain_r": 1.0,
        "q_l": 1.5,
        "q_r": 1.5
      },
      "Band 6": {
        "freq": 630.0,
        "q": 1.0,
        "gain": 0.0,
        "desc": "Fase neutra (630.0 Hz)",
        "gain_l": 0.0,
        "gain_r": 0.0,
        "q_l": 1.0,
        "q_r": 1.0
      },
      "Band 7": {
        "freq": 10080.0,
        "q": 1.0,
        "gain": -0.5,
        "desc": "Atenuación suave de fatiga (10080.0 Hz)",
        "gain_l": -0.5,
        "gain_r": -0.5,
        "q_l": 1.0,
        "q_r": 1.0
      }
    },
    "sub_bands": {},
    "supported_topologies": [
      "2.0",
      "2.1"
    ],
    "sub_supported": true
  },
  {
    "id": "bbc_dip",
    "name": "BBC Dip / Gundry Curve (Monitores LS3/5a / Escucha Relajada)",
    "category": "Música",
    "badge": "BBC Broadcast Gold",
    "description": "Voicing icónico desarrollado por los ingenieros de la British Broadcasting Corporation para los legendarios monitores LS3/5a. Aplica una sutil depresión en 2–4 kHz que elimina la aspereza acústica de las reflexiones de sala.",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Sonido británico aterciopelado y musical.",
      "Voces e instrumentos de cuerda acústicos con calidez insuperable.",
      "Excelente para habitaciones vivas con suelos duros o cristaleras."
    ],
    "cons": [
      "Ligera pérdida de agresividad o ataque en guitarras eléctricas de rock duro."
    ],
    "bands": {
      "Band 1": {
        "freq": 78.7,
        "q": 1.587,
        "gain": -1.5,
        "desc": "Control de graves modal (78.7 Hz)",
        "gain_l": -1.5,
        "gain_r": -1.5,
        "q_l": 1.587,
        "q_r": 1.587
      },
      "Band 2": {
        "freq": 198.4,
        "q": 3.175,
        "gain": -2.0,
        "desc": "Supresión modal de sala (198.4 Hz)",
        "gain_l": -2.0,
        "gain_r": -2.0,
        "q_l": 3.175,
        "q_r": 3.175
      },
      "Band 3": {
        "freq": 396.9,
        "q": 1.587,
        "gain": -3.0,
        "desc": "Atenuación acústica de sala (396.9 Hz)",
        "gain_l": -3.0,
        "gain_r": -3.0,
        "q_l": 1.587,
        "q_r": 1.587
      },
      "Band 4": {
        "freq": 2520.0,
        "q": 1.26,
        "gain": -2.0,
        "desc": "Gundry / BBC Dip en presencia vocal (2520.0 Hz)",
        "gain_l": -2.0,
        "gain_r": -2.0,
        "q_l": 1.26,
        "q_r": 1.26
      },
      "Band 5": {
        "freq": 500.0,
        "q": 1.0,
        "gain": 0.0,
        "desc": "Fase neutra (500.0 Hz)",
        "gain_l": 0.0,
        "gain_r": 0.0,
        "q_l": 1.0,
        "q_r": 1.0
      },
      "Band 6": {
        "freq": 630.0,
        "q": 1.0,
        "gain": 0.0,
        "desc": "Fase neutra (630.0 Hz)",
        "gain_l": 0.0,
        "gain_r": 0.0,
        "q_l": 1.0,
        "q_r": 1.0
      },
      "Band 7": {
        "freq": 10080.0,
        "q": 1.0,
        "gain": -0.5,
        "desc": "Caída suave libre de fatiga (10080.0 Hz)",
        "gain_l": -0.5,
        "gain_r": -0.5,
        "q_l": 1.0,
        "q_r": 1.0
      }
    },
    "sub_bands": {},
    "supported_topologies": [
      "2.0",
      "2.1"
    ],
    "sub_supported": true
  },
  {
    "id": "audiophile_flat",
    "name": "Audiophile Diffuse-Field Flat (Monitoreo de Estudio / Rigor Analítico)",
    "category": "Monitoreo & Puro",
    "badge": "🎯 #7 Respuesta Teórica Plana (EBU Tech 3276 / Studio Monitor)",
    "description": "Respuesta estrictamente plana (0.0 dB) en todo el espectro audible, interviniendo exclusivamente el notch modal en 125 Hz para corregir la física de la sala. Sin realces cosméticos ni edulcorantes tímbricos.",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Máxima fidelidad a la señal fuente sin ninguna alteración tímbrica.",
      "Rigor analítico para detectar fallos de mezcla, ruidos o artefactos.",
      "Respuesta transitoria pura e inalterada en agudos.",
      "Ideal para quienes buscan monitoreo quirúrgico de referencia."
    ],
    "cons": [
      "En salas domésticas con poca absorción puede sonar seco, delgado o 'frío'."
    ],
    "bands": {
      "Band 1": {
        "freq": 396.9,
        "q_l": 1.587,
        "q_r": 1.587,
        "gain_l": -3.5,
        "gain_r": -4.0,
        "desc": "Filtro optimizado 396.9 Hz (common_mode)"
      },
      "Band 2": {
        "freq": 198.4,
        "q_l": 3.175,
        "q_r": 3.175,
        "gain_l": -2.0,
        "gain_r": -2.0,
        "desc": "Filtro optimizado 198.4 Hz (common_mode)"
      },
      "Band 3": {
        "freq": 315.0,
        "q_l": 1.26,
        "q_r": 1.26,
        "gain_l": -3.0,
        "gain_r": 0.0,
        "desc": "Filtro optimizado 315.0 Hz (asym_mode)"
      },
      "Band 4": {
        "freq": 250.0,
        "q_l": 3.175,
        "q_r": 3.175,
        "gain_l": 0.0,
        "gain_r": -5.0,
        "desc": "Filtro optimizado 250.0 Hz (transparent_pass)"
      },
      "Band 5": {
        "freq": 500.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Filtro optimizado 500.0 Hz (inactive)"
      },
      "Band 6": {
        "freq": 630.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Filtro optimizado 630.0 Hz (inactive)"
      },
      "Band 7": {
        "freq": 793.7,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Filtro optimizado 793.7 Hz (inactive)"
      }
    },
    "sub_bands": {},
    "supported_topologies": [
      "2.0",
      "2.1"
    ],
    "sub_supported": true
  },
  {
    "id": "ebu_tech_3276",
    "name": "EBU Tech 3276 Broadcast Reference (Estándar Europeo de Radiodifusión)",
    "category": "Audiófilo",
    "badge": "EBU Tech 3276",
    "description": "Estándar oficial de la European Broadcasting Union (EBU R128 / Tech 3276) para salas de control de audio y emisión. Ofrece respuesta plana en medios y una suave atenuación controlada en agudos para máxima compatibilidad de mezcla.",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Estándar oficial europeo de radiodifusión y televisión.",
      "Garantiza balance tímbrico óptimo entre voz, música y efectos.",
      "Sonido equilibrado y sin artificios."
    ],
    "cons": [
      "Diseñado para rigor técnico más que para espectacularidad efectista."
    ],
    "bands": {
      "Band 1": {
        "freq": 125.0,
        "q": 1.587,
        "gain": -2.0,
        "q_l": 1.587,
        "q_r": 1.587,
        "gain_l": -2.0,
        "gain_r": 0.0,
        "desc": "Modo modal Front L (125.0 Hz) con pase neutro en R"
      },
      "Band 2": {
        "freq": 78.7,
        "q": 2.52,
        "gain": 0.0,
        "q_l": 2.52,
        "q_r": 2.52,
        "gain_l": 0.0,
        "gain_r": -4.0,
        "desc": "Modo modal Front R (78.7 Hz) con pase neutro en L"
      },
      "Band 3": {
        "freq": 31.3,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (31.3 Hz)"
      },
      "Band 4": {
        "freq": 39.4,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (39.4 Hz)"
      },
      "Band 5": {
        "freq": 500.0,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (500.0 Hz)"
      },
      "Band 6": {
        "freq": 630.0,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (630.0 Hz)"
      },
      "Band 7": {
        "freq": 793.7,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (793.7 Hz)"
      }
    },
    "sub_bands": {},
    "supported_topologies": [
      "2.0",
      "2.1"
    ],
    "sub_supported": true
  },
  {
    "id": "loudness_iso226",
    "name": "Loudness Dinámico ISO 226 (Escucha a Bajo Volumen 50-65 dB)",
    "category": "Especial",
    "badge": "ISO 226 Loudness",
    "description": "Aplica los principios de las curvas isofónicas de Fletcher-Munson / ISO 226: compensa la menor sensibilidad del oído humano en bajas y altas frecuencias cuando se escucha a volúmenes bajos o moderados.",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Sonido con cuerpo y pegada completa incluso a volúmenes muy bajos (-35 dB en AVR).",
      "Excelente para trabajar, estudiar o relajarse de día y noche.",
      "Compensa la física del oído sin distorsión."
    ],
    "cons": [
      "A volúmenes muy elevados (+80 dB SPL) puede resultar excesivamente cálido."
    ],
    "bands": {
      "Band 1": {
        "freq": 78.7,
        "q": 1.587,
        "gain": -1.5,
        "desc": "Subgraves limpios para explosiones tácticas (78.7 Hz)",
        "gain_l": -1.5,
        "gain_r": -1.5,
        "q_l": 1.587,
        "q_r": 1.587
      },
      "Band 2": {
        "freq": 198.4,
        "q": 3.175,
        "gain": -2.0,
        "desc": "Supresión modal de sala (198.4 Hz)",
        "gain_l": -2.0,
        "gain_r": -2.0,
        "q_l": 3.175,
        "q_r": 3.175
      },
      "Band 3": {
        "freq": 396.9,
        "q": 1.587,
        "gain": -3.0,
        "desc": "Limpieza espacial para posicionamiento HRTF (396.9 Hz)",
        "gain_l": -3.0,
        "gain_r": -3.0,
        "q_l": 1.587,
        "q_r": 1.587
      },
      "Band 4": {
        "freq": 2520.0,
        "q": 1.26,
        "gain": 1.0,
        "desc": "Localización espacial de pasos y recargas (2520.0 Hz)",
        "gain_l": 1.0,
        "gain_r": 1.0,
        "q_l": 1.26,
        "q_r": 1.26
      },
      "Band 5": {
        "freq": 4000.0,
        "q": 1.5,
        "gain": 1.6,
        "desc": "Claridad de micro-detalle direccional táctico (4000.0 Hz)",
        "gain_l": 1.6,
        "gain_r": 1.6,
        "q_l": 1.5,
        "q_r": 1.5
      },
      "Band 6": {
        "freq": 630.0,
        "q": 1.0,
        "gain": 0.0,
        "desc": "Fase neutra (630.0 Hz)",
        "gain_l": 0.0,
        "gain_r": 0.0,
        "q_l": 1.0,
        "q_r": 1.0
      },
      "Band 7": {
        "freq": 10080.0,
        "q": 1.0,
        "gain": -0.5,
        "desc": "Extensión limpia sin fatiga en sesiones largas (10080.0 Hz)",
        "gain_l": -0.5,
        "gain_r": -0.5,
        "q_l": 1.0,
        "q_r": 1.0
      }
    },
    "sub_bands": {},
    "supported_topologies": [
      "2.0",
      "2.1"
    ],
    "sub_supported": true
  },
  {
    "id": "late_night_whisper",
    "name": "Late Night Whisper (Escucha Nocturna / Anti-Vibración Vecinos)",
    "category": "Especial",
    "badge": "Night Silent Pro",
    "description": "Diseñado para sesiones de cine y música de madrugada. Atenúa severamente las frecuencias subgraves más bajas que se transmiten por la estructura del edificio, manteniendo las voces claras y comprensibles.",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Cero quejas de vecinos por vibraciones transmitidas por paredes o forjados.",
      "Diálogos perfectamente audibles a volumen bajo.",
      "Ideal para dormir a niños o parejas en habitaciones contiguas."
    ],
    "cons": [
      "Elimina el impacto físico visceral del subgrave."
    ],
    "bands": {
      "Band 1": {
        "freq": 78.7,
        "q": 1.587,
        "gain": -3.0,
        "desc": "Atenuación preventiva de subgraves nocturnos (78.7 Hz)",
        "gain_l": -3.0,
        "gain_r": -3.0,
        "q_l": 1.587,
        "q_r": 1.587
      },
      "Band 2": {
        "freq": 198.4,
        "q": 3.175,
        "gain": -3.0,
        "desc": "Corte de resonancia estructural en tabiques (198.4 Hz)",
        "gain_l": -3.0,
        "gain_r": -3.0,
        "q_l": 3.175,
        "q_r": 3.175
      },
      "Band 3": {
        "freq": 396.9,
        "q": 1.587,
        "gain": -3.5,
        "desc": "Limpieza de retumbo nocturno (396.9 Hz)",
        "gain_l": -3.5,
        "gain_r": -3.5,
        "q_l": 1.587,
        "q_r": 1.587
      },
      "Band 4": {
        "freq": 2520.0,
        "q": 1.26,
        "gain": 2.5,
        "desc": "Compensación Fletcher-Munson en diálogo a bajo volumen (2520.0 Hz)",
        "gain_l": 2.5,
        "gain_r": 2.5,
        "q_l": 1.26,
        "q_r": 1.26
      },
      "Band 5": {
        "freq": 500.0,
        "q": 1.0,
        "gain": 0.0,
        "desc": "Fase neutra (500.0 Hz)",
        "gain_l": 0.0,
        "gain_r": 0.0,
        "q_l": 1.0,
        "q_r": 1.0
      },
      "Band 6": {
        "freq": 630.0,
        "q": 1.0,
        "gain": 0.0,
        "desc": "Fase neutra (630.0 Hz)",
        "gain_l": 0.0,
        "gain_r": 0.0,
        "q_l": 1.0,
        "q_r": 1.0
      },
      "Band 7": {
        "freq": 10080.0,
        "q": 1.0,
        "gain": -1.5,
        "desc": "Suavizado de agudos para evitar sobresaltos (10080.0 Hz)",
        "gain_l": -1.5,
        "gain_r": -1.5,
        "q_l": 1.0,
        "q_r": 1.0
      }
    },
    "sub_bands": {},
    "supported_topologies": [
      "2.0",
      "2.1"
    ],
    "sub_supported": true
  },
  {
    "id": "pure_bookshelf_stereo",
    "name": "Pure Bookshelf Stereo (Q Acoustics 3020i Full-Range Sin Subwoofer)",
    "category": "Audiófilo",
    "badge": "Pure Stereo 2.0",
    "description": "Calibración pura para los altavoces de estantería Q Acoustics 3020i trabajando en rango completo sin asistencia de subwoofer. Protege el cono de 5 pulgadas por debajo de su sintonía bass-reflex (fc = 64 Hz).",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Sonido puro e integrado de dos cajas acústicas sin problemas de fase de subwoofer.",
      "Protege los woofers de 5 pulgadas contra excursión dañina bajo 64 Hz.",
      "Escenario sonoro estéreo coherente y natural."
    ],
    "cons": [
      "Extensión limitada en el subgrave profundo (<60 Hz) debido a la física del altavoz."
    ],
    "bands": {
      "Band 1": {
        "freq": 78.7,
        "q": 2.52,
        "gain": -2.0,
        "q_l": 2.52,
        "q_r": 2.52,
        "gain_l": 0.0,
        "gain_r": -2.0,
        "desc": "Supresión resonancia de sala en estéreo (78.7 Hz)"
      },
      "Band 2": {
        "freq": 2520.0,
        "q": 1.26,
        "gain": 1.5,
        "q_l": 1.26,
        "q_r": 1.26,
        "gain_l": 1.5,
        "gain_r": 1.5,
        "desc": "Compensación de cruce Q Acoustics 3020i (2.5 kHz)"
      },
      "Band 3": {
        "freq": 10080.0,
        "q": 1.0,
        "gain": -1.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": -1.0,
        "gain_r": -1.0,
        "desc": "Atenuación suave agudos de sala (10 kHz)"
      },
      "Band 4": {
        "freq": 12700.0,
        "q": 1.0,
        "gain": 2.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 2.0,
        "gain_r": 2.0,
        "desc": "Aire armónico en altas frecuencias (12.7 kHz)"
      },
      "Band 5": {
        "freq": 4000.0,
        "q": 1.26,
        "gain": -4.5,
        "q_l": 1.26,
        "q_r": 1.26,
        "gain_l": -4.5,
        "gain_r": -4.5,
        "desc": "Atenuación de elevación acústica de sala (4 kHz)"
      },
      "Band 6": {
        "freq": 500.0,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Pase neutro medios"
      },
      "Band 7": {
        "freq": 630.0,
        "q": 1.0,
        "gain": 0.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Pase neutro medios"
      }
    },
    "sub_bands": {},
    "supported_topologies": [
      "2.0"
    ],
    "sub_supported": false
  },
  {
    "id": "harman_2_1",
    "name": "Harman 2.1 (Focal Cub Evo)",
    "category": "Música Hi-Fi",
    "badge": "⚡ Sistema 2.1 (Focal Cub Evo + Q Acoustics 3020i)",
    "description": "Sistema 2.1 con crossover activo a 80 Hz. Frontales Small, sub corregido por sala.",
    "cutoff_hz": 64.0,
    "subwoofer_crossover_hz": 80.0,
    "pros": [
      "Graves profundos y articulados sin sobrecargar los conos de los satélites.",
      "Crossover acústico óptimo a 80 Hz.",
      "Supresión quirúrgica de resonancias modales en el subwoofer."
    ],
    "cons": [
      "Requiere que el subwoofer Focal Cub Evo esté conectado."
    ],
    "bands": {
      "Band 1": {
        "freq": 315.0,
        "q_l": 0.5,
        "q_r": 0.5,
        "gain_l": 0.0,
        "gain_r": -2.5,
        "desc": "Modo modal Front R (315.0 Hz) con pase neutro en L"
      },
      "Band 2": {
        "freq": 78.7,
        "q_l": 0.5,
        "q_r": 0.5,
        "gain_l": 0.0,
        "gain_r": -2.0,
        "desc": "Modo modal Front R (78.7 Hz) con pase neutro en L"
      },
      "Band 3": {
        "freq": 31.3,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (31.3 Hz)"
      },
      "Band 4": {
        "freq": 39.4,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (39.4 Hz)"
      },
      "Band 5": {
        "freq": 500.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (500.0 Hz)"
      },
      "Band 6": {
        "freq": 630.0,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (630.0 Hz)"
      },
      "Band 7": {
        "freq": 793.7,
        "q_l": 1.0,
        "q_r": 1.0,
        "gain_l": 0.0,
        "gain_r": 0.0,
        "desc": "Preservación anecoica / Fase neutra (793.7 Hz)"
      }
    },
    "sub_bands": {
      "Band 1": {
        "freq": 78.7,
        "q": 5.04,
        "gain": -3.5,
        "role": "sub_modal_resonance",
        "desc": "Modo modal Subwoofer Focal Cub Evo (78.7 Hz)"
      }
    },
    "supported_topologies": [
      "2.0",
      "2.1"
    ],
    "sub_supported": true
  }
];

export const DEFAULT_TARGETS_MAP: Record<string, TargetProfile> = Object.fromEntries(
  DEFAULT_TARGET_PROFILES.map(p => [p.id, p])
);
