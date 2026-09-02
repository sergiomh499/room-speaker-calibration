# Fundamentos Psicoacústicos y Perfiles de Calibración

Este documento detalla las bases científicas, investigaciones académicas de referencia y la justificación psicoacústica detrás de las curvas objetivo implementadas en el sistema de calibración para la combinación de la **LG C5 OLED**, el **Yamaha RX-V673** y los **Q Acoustics 3020i**.

---

## 1. El Mito de la «Respuesta Plana en Sala»

Una creencia común pero errónea en la ingeniería de sonido es que una respuesta en frecuencia estrictamente plana ($0\text{ dB}$ en todo el espectro medido en el punto de escucha) produce el sonido más fiel.

Las investigaciones del **Dr. Floyd Toole** y el **Dr. Sean Olive** (*Audio Engineering Society* - AES) demuestran lo contrario:
1. **Directividad y Absorción Natural**: Un altavoz anecoicamente plano proyecta más energía en bajas frecuencias que en altas debido a que los graves son omnidireccionales ($4\pi$) mientras que los agudos son direccionales ($2\pi$).
2. **Absorción de la Sala**: Los materiales domésticos (alfombras, sofás, cortinas, aire) absorben más energía acústica a altas frecuencias.
3. **Conclusión**: Una curva percibida como natural y equilibrada en una sala doméstica **debe tener una pendiente descendente constante (Roll-off)** desde los graves hasta los agudos (típicamente de $-0.8\text{ dB}$ a $-1.2\text{ dB}$ por octava por encima de 2 kHz).

---

## 2. Contornos de Igual Sonoridad (ISO 226 / Fletcher-Munson)

La sensibilidad del oído humano no es lineal:
* A volúmenes moderados de escucha doméstica (65 dB a 75 dB SPL), el oído es notablemente menos sensible a las frecuencias por debajo de 100 Hz.
* Para percibir los bombos, el bajo eléctrico y las explosiones con el mismo impacto que en un concierto o una sala de cine comercial calibrada a 85 dB SPL, la curva debe incorporar un **realce de graves controlado (+4 dB a +6 dB por debajo de 90 Hz)** que corte limpiamente antes de los 200 Hz para no enturbiar las frecuencias vocales.

---

## 3. Frecuencia de Transición o Límite de Schroeder ($f_s$)

En cualquier sala de escucha existen dos dominios acústicos diferenciados:
$$\text{Frecuencia de Schroeder } (f_s) \approx 2000 \sqrt{\frac{T_{60}}{V}}$$
En salas residenciales estándar, $f_s$ se sitúa entre **200 Hz y 250 Hz**.

| Dominio | Rango de Frecuencias | Comportamiento Físico | Regla de Ecualización (PEQ) |
| :--- | :--- | :--- | :--- |
| **Bajo Schroeder** ($< f_s$) | $20\text{ Hz} - 250\text{ Hz}$ | **Ondas Estacionarias y Modos de Sala**: La sala domina el sonido creando picos y valles de resonancia. | **Corrección Obligatoria**: Se deben aplicar filtros paramétricos estrechos (Q alto) para recortar resonancias. |
| **Alto Schroeder** ($> f_s$) | $> 250\text{ Hz}$ | **Sonido Directo y Reflexiones Tempranas**: El altavoz domina la percepción tímbrica. | **No Sobre-ecualizar**: No corregir valles estrechos; solo aplicar compensaciones suaves de ancho de banda amplio (Q bajo). |

---

## 4. Catálogo de Curvas Objetivo en el Repositorio

### A. `harman_impact` (Harman Impact Reference — 🏆 Recomendado Definitivo)
* **Graves**: $+3.0\text{ dB}$ en 62.5 Hz y $-4.0\text{ dB}$ en 99.2 Hz (Front R) para eliminar el retumbo de esquina y ganar pegada física.
* **Medios**: $+1.5\text{ dB}$ en 2.52 kHz (Q=1.260) compensando el escalón anecoico del filtro divisor de los 3020i (efecto holográfico de voces).
* **Agudos**: Caída suave de $-1.0\text{ dB}$ en 10.1 kHz (*Harman House Curve*).
* **Uso**: Todo tipo de música y películas con máxima pegada y cero fatiga.

### B. `harman_neutral` (Harman Reference Analítica)
* Curva clásica balanceada con menor ganancia en el extremo grave (+1.5 dB en 62.5 Hz). Ideal para música acústica y audiciones críticas.

### C. `cinema_impact` (Blockbuster Cine de Acción)
* Máxima presión en subgraves (+3.0 dB) y caída pronunciada en agudos (-1.2 dB/octava >5 kHz) para explosiones espectaculares sin dureza.

### D. `vocal_clarity` (Podcasts, YouTube, Noche)
* Enfoque de energía en el rango de 300 Hz a 4 kHz; combina con `Drama DSP` y `Adaptive DRC: Auto` para entender cada susurro de madrugada.

### E. `warm_music` (Calidez Analógica Británica / Vinilos)
* Graves redondos en 100-150 Hz y agudos atenuados para discos antiguos o grabaciones brillantes de los 70/80.
