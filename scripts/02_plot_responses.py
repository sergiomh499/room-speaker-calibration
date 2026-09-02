import numpy as np
import matplotlib.pyplot as plt

data_path = "/home/sergio/room-speaker-calibration/data/medicion_real_calibracion.npz"
data = np.load(data_path)

freqs = data['freqs']
raw_l = data['raw_l']
smooth_l = data['smooth_l']
raw_r = data['raw_r']
smooth_r = data['smooth_r']
ir_l = data['ir_l']
ir_r = data['ir_r']

plt.style.use('dark_background')

# 1. Main Frequency Response & Stereo Symmetry Figure
fig, axs = plt.subplots(2, 2, figsize=(15, 10), dpi=140)
fig.suptitle("Respuesta Acústica Real Medida en Sala: Front L vs Front R\nYamaha RX-V673 + Q Acoustics 3020i (PEQ Manual Activo)", 
             fontsize=14, fontweight='bold', color='#4fc3f7', y=0.98)

mask = (freqs >= 25) & (freqs <= 18000)
f_plot = freqs[mask]

# Subplot 1: Left Channel
ax1 = axs[0, 0]
ax1.semilogx(f_plot, raw_l[mask], color='#4caf50', alpha=0.35, lw=1.0, label='Raw (FFT 65k)')
ax1.semilogx(f_plot, smooth_l[mask], color='#00e676', lw=2.2, label='Suavizado (1/24 Octava)')
ax1.axhline(0, color='gray', linestyle='--', alpha=0.5)
ax1.set_title("Canal Izquierdo (Front L - Abierto)", fontsize=11.5, color='#e0e0e0')
ax1.set_xlabel("Frecuencia (Hz)")
ax1.set_ylabel("Magnitud Normalizada (dB SPL)")
ax1.set_xlim(25, 18000)
ax1.set_ylim(-20, 15)
ax1.grid(True, which='both', ls=':', alpha=0.3)
ax1.legend(loc='lower right', fontsize=9)

# Subplot 2: Right Channel
ax2 = axs[0, 1]
ax2.semilogx(f_plot, raw_r[mask], color='#29b6f6', alpha=0.35, lw=1.0, label='Raw (FFT 65k)')
ax2.semilogx(f_plot, smooth_r[mask], color='#00b0ff', lw=2.2, label='Suavizado (1/24 Octava)')
ax2.axhline(0, color='gray', linestyle='--', alpha=0.5)
ax2.set_title("Canal Derecho (Front R - Esquina)", fontsize=11.5, color='#e0e0e0')
ax2.set_xlabel("Frecuencia (Hz)")
ax2.set_ylabel("Magnitud Normalizada (dB SPL)")
ax2.set_xlim(25, 18000)
ax2.set_ylim(-20, 15)
ax2.grid(True, which='both', ls=':', alpha=0.3)
ax2.legend(loc='lower right', fontsize=9)

# Subplot 3: Stereo Balance (|L - R|)
ax3 = axs[1, 0]
diff_smooth = np.abs(smooth_l[mask] - smooth_r[mask])
mean_diff = np.mean(diff_smooth)
ax3.semilogx(f_plot, diff_smooth, color='#ffd54f', lw=2.0, label=f'Desbalance |L - R| (Media: {mean_diff:.2f} dB)')
ax3.axhline(1.0, color='#76ff03', linestyle=':', lw=1.5, alpha=0.8, label='Objetivo de Referencia (±1 dB)')
ax3.set_title("Simetría Estéreo Real (Diferencia Absoluta entre Canales)", fontsize=11.5, color='#e0e0e0')
ax3.set_xlabel("Frecuencia (Hz)")
ax3.set_ylabel("Diferencia (dB)")
ax3.set_xlim(25, 18000)
ax3.set_ylim(0, 10)
ax3.grid(True, which='both', ls=':', alpha=0.3)
ax3.legend(loc='upper right', fontsize=9)

# Subplot 4: Detail in Bass Region (30 Hz - 400 Hz)
ax4 = axs[1, 1]
mask_bass = (freqs >= 30) & (freqs <= 400)
ax4.plot(freqs[mask_bass], smooth_l[mask_bass], color='#00e676', lw=2.0, label='Front L (Suavizado 1/24)')
ax4.plot(freqs[mask_bass], smooth_r[mask_bass], color='#00b0ff', lw=2.0, label='Front R (Suavizado 1/24)')
ax4.axhline(0, color='gray', linestyle='--', alpha=0.5)
ax4.set_title("Detalle Zona de Graves (30 Hz - 400 Hz)", fontsize=11.5, color='#e0e0e0')
ax4.set_xlabel("Frecuencia (Hz)")
ax4.set_ylabel("Magnitud (dB)")
ax4.set_xlim(30, 400)
ax4.grid(True, which='both', ls=':', alpha=0.3)
ax4.legend(loc='lower right', fontsize=9)

plt.tight_layout()
fig_path = "/home/sergio/room-speaker-calibration/figures/respuesta_acustica_real.png"
plt.savefig(fig_path, dpi=140)
plt.close()

# 2. Impulse Response Figure
fig_ir, axs_ir = plt.subplots(2, 1, figsize=(12, 6), dpi=130)
fig_ir.suptitle("Respuesta al Impulso Medida (Deconvolución de Farina)", fontsize=12, fontweight='bold', color='#4fc3f7')

t_ir = np.arange(len(ir_l)) / 48000.0 * 1000.0 # in ms
axs_ir[0].plot(t_ir[:1000], ir_l[:1000], color='#00e676', lw=1.2)
axs_ir[0].set_title("Impulse Response - Canal Izquierdo (Front L)", fontsize=10, color='#e0e0e0')
axs_ir[0].set_xlabel("Tiempo (ms)")
axs_ir[0].set_ylabel("Amplitud Lineal")
axs_ir[0].grid(True, ls=':', alpha=0.3)

axs_ir[1].plot(t_ir[:1000], ir_r[:1000], color='#00b0ff', lw=1.2)
axs_ir[1].set_title("Impulse Response - Canal Derecho (Front R)", fontsize=10, color='#e0e0e0')
axs_ir[1].set_xlabel("Tiempo (ms)")
axs_ir[1].set_ylabel("Amplitud Lineal")
axs_ir[1].grid(True, ls=':', alpha=0.3)

plt.tight_layout()
fig_ir_path = "/home/sergio/room-speaker-calibration/figures/respuesta_impulso_real.png"
plt.savefig(fig_ir_path, dpi=130)
plt.close()

print(f"Figuras reales guardadas en /home/sergio/room-speaker-calibration/figures/")
print(f"Métricas reales calculadas:")
print(f" - Desbalance Estéreo Medio (|L - R|): {mean_diff:.2f} dB")
eval_mask = (freqs >= 60) & (freqs <= 15000)
print(f" - Desviación Estándar Front L: ±{np.std(smooth_l[eval_mask]):.2f} dB")
print(f" - Desviación Estándar Front R: ±{np.std(smooth_r[eval_mask]):.2f} dB")
