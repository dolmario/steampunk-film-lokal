"""Zustandsbericht vor einem GPU-Lauf: Prozesse mit Startzeit, belegte Ports, freier RAM, GPU-Speicher.

Schreibt messung/guard-<Zeit>.json und gibt eine Zusammenfassung aus. Endet mit Code 1, wenn Port 8189 belegt ist oder
weniger als MIN_FREI_GB RAM frei sind. Es werden keine Prozesse verändert.

Aufruf: python guard_vor_start.py [--port 8189] [--min-frei-gb 12]
"""
import argparse
import json
import socket
import subprocess
import time

import os
import sys

# Eingebettetes Python (ComfyUI Portable) hat den Skriptordner nicht im Suchpfad.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lib


def powershell(befehl):
    return subprocess.run(["powershell", "-NoProfile", "-Command", befehl], capture_output=True, text=True).stdout


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8189)
    p.add_argument("--min-frei-gb", type=float, default=12)
    a = p.parse_args()
    prozesse = json.loads(powershell(
        "Get-CimInstance Win32_Process | Where-Object { $_.WorkingSet -gt 500MB -or $_.CommandLine -match 'main.py|llama|comfy|moss|render' } | "
        "Select-Object ProcessId,ParentProcessId,Name,CreationDate,WorkingSetSize,@{n='Cmd';e={([string]$_.CommandLine).Substring(0,[Math]::Min(160,([string]$_.CommandLine).Length))}} | "
        "ConvertTo-Json -Compress -Depth 3") or "[]")
    if isinstance(prozesse, dict):
        prozesse = [prozesse]
    frei_gb = round(float(powershell("(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory").strip().replace(",", ".")) / 1048576, 1)
    with socket.socket() as sock:
        sock.settimeout(3)
        port_belegt = sock.connect_ex(("127.0.0.1", a.port)) == 0
    gpu = powershell("(Get-Counter '\\GPU Adapter Memory(*)\\Dedicated Usage' -ErrorAction SilentlyContinue).CounterSamples | "
                     "Sort-Object CookedValue -Descending | Select-Object -First 1 -ExpandProperty CookedValue").strip()
    bericht = {"zeit": time.strftime("%Y-%m-%d %H:%M:%S"), "port": a.port, "port_belegt": port_belegt, "ram_frei_gb": frei_gb,
               "gpu_dediziert_bytes": gpu, "grosse_prozesse": prozesse}
    ziel = lib.WURZEL / "messung" / f"guard-{time.strftime('%Y%m%d-%H%M%S')}.json"
    ziel.write_text(json.dumps(bericht, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Guard: Port {a.port} {'BELEGT' if port_belegt else 'frei'}, RAM frei {frei_gb} GB, GPU belegt {gpu or 'unbekannt'} Byte, "
          f"{len(prozesse)} große/relevante Prozesse, Bericht {ziel.name}")
    if port_belegt or frei_gb < a.min_frei_gb:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
