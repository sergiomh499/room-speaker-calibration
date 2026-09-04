#!/usr/bin/env python3
"""Multi-format PEQ filter export engine (REW, EqualizerAPO, CSV, ZIP).

Exports mathematically optimized 7-band PEQ parameters to standard audio DSP formats.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
from pathlib import Path
import time
import zipfile
import sys
REPO_DIR = Path(__file__).resolve().parent.parent
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))
REPO_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_DIR / "config"
DATA_DIR = REPO_DIR / "data"
DEFAULT_EXPORT_DIR = REPO_DIR / "exports"


def load_active_hardware() -> dict[str, str]:
    """Load active equipment identifiers from config/hardware.json."""
    hw_path = CONFIG_DIR / "hardware.json"
    if hw_path.exists():
        try:
            with open(hw_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("active", {})
        except Exception:
            pass
    return {
        "microphone": "pixel_9_pro_calibrated",
        "amplifier": "yamaha_rx_v673",
        "speakers": "q_acoustics_3020i",
    }


def get_profile_filters(profile: str = "harman_wide_room") -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Retrieve 7-band filters for Front L and Front R for a given target profile.

    Attempts to load from optimized calibration data or auto_calibrate calculation.
    """
    import numpy as np

    # Check for precomputed verification or calibration data
    data_file = DATA_DIR / f"medicion_verificacion_manual_{profile}.npz"
    if not data_file.exists():
        data_file = DATA_DIR / "medicion_promedio_espacial.npz"
    if not data_file.exists():
        data_file = DATA_DIR / "medicion_real_calibracion.npz"

    # Fallback to standard discrete matrix if file not ready
    if not data_file.exists():
        # Canonical baseline bands for fallback
        bands_l = [
            {"band": 1, "freq_hz": 2520.0, "q": 1.260, "gain_db": 1.5, "type": "PK"},
            {"band": 2, "freq_hz": 125.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 3, "freq_hz": 315.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 4, "freq_hz": 793.7, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 5, "freq_hz": 2000.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 6, "freq_hz": 5040.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 7, "freq_hz": 12700.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        ]
        bands_r = [
            {"band": 1, "freq_hz": 198.4, "q": 0.500, "gain_db": -2.0, "type": "PK"},
            {"band": 2, "freq_hz": 2520.0, "q": 1.260, "gain_db": 2.0, "type": "PK"},
            {"band": 3, "freq_hz": 315.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 4, "freq_hz": 793.7, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 5, "freq_hz": 2000.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 6, "freq_hz": 5040.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 7, "freq_hz": 12700.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        ]
        return bands_l, bands_r

    # Use auto_calibrate run_calibration logic directly
    try:
        from scripts.auto_calibrate import run_calibration
        opt_res = run_calibration(target_key=profile, push_yamaha=False)
        left_bands = opt_res.get("left_bands", [])
        right_bands = opt_res.get("right_bands", [])
        if left_bands and right_bands:
            bands_l = [
                {"band": i + 1, "freq_hz": float(b[0]), "q": float(b[1]), "gain_db": float(b[2]), "type": "PK"}
                for i, b in enumerate(left_bands)
            ]
            bands_r = [
                {"band": i + 1, "freq_hz": float(b[0]), "q": float(b[1]), "gain_db": float(b[2]), "type": "PK"}
                for i, b in enumerate(right_bands)
            ]
            return bands_l, bands_r
    except Exception as e:
        print(f"[Aviso] No se pudo ejecutar run_calibration en directo ({e}), usando fallback.")

    # Fallback to standard canonical layout
    bands_l = [
        {"band": 1, "freq_hz": 2520.0, "q": 1.260, "gain_db": 1.5, "type": "PK"},
        {"band": 2, "freq_hz": 125.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        {"band": 3, "freq_hz": 315.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        {"band": 4, "freq_hz": 793.7, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        {"band": 5, "freq_hz": 2000.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        {"band": 6, "freq_hz": 5040.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        {"band": 7, "freq_hz": 12700.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
    ]
    bands_r = [
        {"band": 1, "freq_hz": 198.4, "q": 0.500, "gain_db": -2.0, "type": "PK"},
        {"band": 2, "freq_hz": 2520.0, "q": 1.260, "gain_db": 2.0, "type": "PK"},
        {"band": 3, "freq_hz": 315.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        {"band": 4, "freq_hz": 793.7, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        {"band": 5, "freq_hz": 2000.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        {"band": 6, "freq_hz": 5040.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        {"band": 7, "freq_hz": 12700.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
    ]
    return bands_l, bands_r


def format_rew(
    bands: list[dict[str, Any]],
    channel: str = "L",
    profile: str = "harman_wide_room",
    hardware: dict[str, str] | None = None,
) -> str:
    """Format single-channel filters according to Room EQ Wizard (.req) specification."""
    hw = hardware or load_active_hardware()
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "Filter Settings file",
        "",
        "Room EQ V5.20 or later",
        f"Dated: {now_str}",
        f"Notes: Room Speaker Calibration - Profile: {profile} - Channel: {channel}",
        f"Hardware: Mic: {hw.get('microphone', 'N/A')} | Amp: {hw.get('amplifier', 'N/A')} | Speakers: {hw.get('speakers', 'N/A')}",
        "",
        "Equaliser: Generic",
    ]

    for b in bands:
        idx = b.get("band", 1)
        freq = float(b.get("freq_hz", 1000.0))
        gain = float(b.get("gain_db", 0.0))
        q = float(b.get("q", 1.0))
        # Format matching exact REW syntax:
        # Filter  1: ON  PK       Fc   2520.0 Hz  Gain  +1.5 dB  Q 1.260
        state = "ON "
        lines.append(
            f"Filter {idx:2d}: {state} PK       Fc {freq:8.1f} Hz  Gain {gain:+6.1f} dB  Q {q:5.3f}"
        )

    return "\n".join(lines) + "\n"


def format_equalizer_apo(
    bands_l: list[dict[str, Any]],
    bands_r: list[dict[str, Any]],
    profile: str = "harman_wide_room",
    hardware: dict[str, str] | None = None,
) -> str:
    """Format dual-channel config for EqualizerAPO with negative preamp headroom."""
    hw = hardware or load_active_hardware()
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    # Calculate digital headroom to prevent clipping on positive gains
    max_gain_l = max([b.get("gain_db", 0.0) for b in bands_l], default=0.0)
    max_gain_r = max([b.get("gain_db", 0.0) for b in bands_r], default=0.0)
    max_boost = max(0.0, max_gain_l, max_gain_r)
    preamp_offset = -max_boost

    lines = [
        "# EqualizerAPO Configuration",
        f"# Generated: {now_str}",
        f"# Target Profile: {profile}",
        f"# System: {hw.get('microphone')} / {hw.get('amplifier')} / {hw.get('speakers')}",
        "",
        f"# Headroom digital para prevenir clipping (max boost: +{max_boost:.1f} dB)",
        f"Preamp: {preamp_offset:+.1f} dB",
        "",
        "Channel: L",
    ]

    for b in bands_l:
        idx = b.get("band", 1)
        freq = float(b.get("freq_hz", 1000.0))
        gain = float(b.get("gain_db", 0.0))
        q = float(b.get("q", 1.0))
        lines.append(f"Filter {idx}: ON PK Fc {freq:.1f} Hz Gain {gain:+.1f} dB Q {q:.3f}")

    lines.extend(["", "Channel: R"])

    for b in bands_r:
        idx = b.get("band", 1)
        freq = float(b.get("freq_hz", 1000.0))
        gain = float(b.get("gain_db", 0.0))
        q = float(b.get("q", 1.0))
        lines.append(f"Filter {idx}: ON PK Fc {freq:.1f} Hz Gain {gain:+.1f} dB Q {q:.3f}")

    return "\n".join(lines) + "\n"


def format_csv(
    bands_l: list[dict[str, Any]],
    bands_r: list[dict[str, Any]],
    profile: str = "harman_wide_room",
    hardware: dict[str, str] | None = None,
) -> str:
    """Format PEQ parameters into tabular CSV string."""
    hw = hardware or load_active_hardware()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "channel",
        "band",
        "frequency_hz",
        "gain_db",
        "q",
        "filter_type",
        "profile",
        "hardware_mic",
        "hardware_amp",
        "hardware_speakers",
    ])

    for ch, bands in (("L", bands_l), ("R", bands_r)):
        for b in bands:
            writer.writerow([
                ch,
                b.get("band", 1),
                f"{float(b.get('freq_hz', 1000.0)):.1f}",
                f"{float(b.get('gain_db', 0.0)):.1f}",
                f"{float(b.get('q', 1.0)):.3f}",
                b.get("type", "PK"),
                profile,
                hw.get("microphone", ""),
                hw.get("amplifier", ""),
                hw.get("speakers", ""),
            ])

    return output.getvalue()


def build_export_bundle(
    profile: str = "harman_wide_room",
    out_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Generate all format strings and optionally persist to disk."""
    hw = load_active_hardware()
    bands_l, bands_r = get_profile_filters(profile)

    rew_l = format_rew(bands_l, channel="L", profile=profile, hardware=hw)
    rew_r = format_rew(bands_r, channel="R", profile=profile, hardware=hw)
    apo = format_equalizer_apo(bands_l, bands_r, profile=profile, hardware=hw)
    csv_text = format_csv(bands_l, bands_r, profile=profile, hardware=hw)

    # In-memory zip creation
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"filters_{profile}_L.req", rew_l)
        zf.writestr(f"filters_{profile}_R.req", rew_r)
        zf.writestr(f"equalizer_apo_{profile}.txt", apo)
        zf.writestr(f"peq_filters_{profile}.csv", csv_text)

    zip_bytes = zip_buffer.getvalue()

    # Save to disk if destination directory provided
    if out_dir:
        dest = Path(out_dir)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / f"filters_{profile}_L.req").write_text(rew_l, encoding="utf-8")
        (dest / f"filters_{profile}_R.req").write_text(rew_r, encoding="utf-8")
        (dest / f"equalizer_apo_{profile}.txt").write_text(apo, encoding="utf-8")
        (dest / f"peq_filters_{profile}.csv").write_text(csv_text, encoding="utf-8")
        (dest / f"filters_{profile}_all.zip").write_bytes(zip_bytes)

    return {
        "profile": profile,
        "hardware": hw,
        "rew_l": rew_l,
        "rew_r": rew_r,
        "equalizer_apo": apo,
        "csv": csv_text,
        "zip_bytes": zip_bytes,
    }


def main():
    parser = argparse.ArgumentParser(description="Multi-format PEQ filter export utility.")
    parser.add_argument(
        "--profile",
        default="harman_wide_room",
        help="Target acoustic profile key (e.g. harman_wide_room, bk_1974).",
    )
    parser.add_argument(
        "--format",
        choices=["rew", "equalizerapo", "csv", "all"],
        default="all",
        help="Output export format (rew, equalizerapo, csv, all).",
    )
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_EXPORT_DIR),
        help="Destination directory for exported files.",
    )
    args = parser.parse_args()

    dest = Path(args.out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    bundle = build_export_bundle(profile=args.profile, out_dir=dest)

    print(f"[v] Filtros PEQ exportados con éxito para perfil '{args.profile}' en '{dest}':")
    if args.format in ("rew", "all"):
        print(f"  - {dest}/filters_{args.profile}_L.req")
        print(f"  - {dest}/filters_{args.profile}_R.req")
    if args.format in ("equalizerapo", "all"):
        print(f"  - {dest}/equalizer_apo_{args.profile}.txt")
    if args.format in ("csv", "all"):
        print(f"  - {dest}/peq_filters_{args.profile}.csv")
    if args.format == "all":
        print(f"  - {dest}/filters_{args.profile}_all.zip")


if __name__ == "__main__":
    main()
