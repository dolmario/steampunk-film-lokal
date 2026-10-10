# Die Schwestern von Messingbrunn

[English](README.en.md)

Ein Steampunk-Kurzfilm, komplett lokal erzeugt: 36 Einstellungen à 5 Sekunden. Eine riesige Dampf-Spinne bedroht die Stadt Messingbrunn, die Schwestern Elara und Mira bauen eine Aether-Spule. Dieses Paket erzeugt den ganzen Film von null auf deinem Rechner: Figuren, Standbilder, Clips und Rohschnitt. Ändern musst du nur Text (siehe [PROMPTS-AENDERN.md](PROMPTS-AENDERN.md)).

Enthalten sind Skripte, Geschichte und Workflows. Nicht enthalten sind Modellgewichte, fertige Bilder und die Musik aus dem Video.

## Was wir auf drei Rechnern gemacht haben

Gleiche Skripte, gleiche Geschichte, Seed 11. Zeiten aus den Messdateien (`messung/beispiele/drei-rechner.csv`).

| Rechner | Speicher | Bilder | Clip im Mittel | Ganzer Film von null |
|---|---|---|---|---|
| GMKtec EVO-X2 (AMD Strix Halo, Radeon 8060S) | gemeinsamer Speicher | FLUX.2 Klein 4B | 436 s (397–466) | nicht von null gemessen; 36 Clips: Rechenzeit 4 h 22 min, Laufzeit mit Neustarts 4 h 35 min |
| NVIDIA RTX 3080 Ti | 12 GB VRAM, 16 GB RAM | FLUX.2 Klein 4B, 13 s je Bild | 252 s (245–295) | 2 h 55 min |
| NVIDIA RTX 3090 Ti | 24 GB VRAM, 32 GB RAM | FLUX.2 Klein 4B, 8,5 s je Bild | 102 s (90–112) | 1 h 29 min |
| NVIDIA RTX 3090 Ti | 24 GB VRAM, 32 GB RAM | FLUX.2 dev (GGUF Q4_K_M), 242 s je Bild | 90 s (90–96) | 3 h 47 min |

Alle Läufe: 36 von 36 Clips ohne Abbruch und ohne Wiederholung. Die RTX 3080 Ti ist an der Grenze: VRAM-Spitze 12 068 von 12 288 MiB, freier RAM minimal 3,9 GB. Der FLUX.2-dev-Lauf ließ auf 32 GB RAM nur 0,9 GB frei. Nicht getestet: Karten unter 12 GB VRAM, unter 16 GB RAM, Linux, Mac.


## So startest du

1. **ComfyUI** installieren (getestet: ComfyUI 0.38.0; auf NVIDIA die Windows-Portable-Fassung, auf dem EVO-X2 ComfyUI mit ROCm für Windows).
2. **Modelle** aus der Tabelle unten in die ComfyUI-Ordner legen. Das Paket lädt nichts selbst herunter.
3. **ffmpeg** und **ffprobe** müssen im Pfad sein (`ffmpeg -version` muss antworten).
4. In der Eingabeaufforderung (Pfade anpassen):
   ```text
   set COMFYUI_DIR=C:\Pfad\ComfyUI_windows_portable\ComfyUI
   set COMFYUI_PYTHON=C:\Pfad\ComfyUI_windows_portable\python_embeded\python.exe
   START-SELBSTLAEUFER.cmd
   ```
   Optional vorher: `set MODELL=dev` (FLUX.2 dev statt Klein 4B) oder `set GERAET=meinpc` (Name der Messdatei).
5. Warten. Am Ende liegen `bilder\`, `clips\` und `film_roh.mp4` (ohne Ton) im Ordner, die Messwerte in `messung\<Gerät>.jsonl`.

Der Selbstläufer startet sein eigenes ComfyUI auf Port 8189, für jeden Clip frisch und mit `--disable-pinned-memory`. Ohne diese Option lieferte LTX-2.5 bei uns graues Rauschen oder brach beim Laden ab. Port 8189 muss frei sein; der Selbstläufer beendet keine fremden Programme. Browser, Spiele und andere KI-Programme vorher schließen.

## Eigene Geschichte

`story/figuren.json` beschreibt die Figuren, `story/shots.json` die 36 Einstellungen (`bild`, `bewegung`, `figuren`). Nach einer Änderung rechnet der nächste Start nur das Betroffene neu: geänderte `bewegung` nur den Clip, geändertes `bild` Standbild und Clip, eine geänderte Figur ihre Referenzen und alle Einstellungen mit ihr. Alte Dateien wandern in `alt_...`-Ordner. Details: [PROMPTS-AENDERN.md](PROMPTS-AENDERN.md).

## Modelle und Lizenzen

Die Dateinamen stehen in `runner/ablaeufe.py`.

| Aufgabe | Dateien | Quelle | Lizenz laut Quelle |
|---|---|---|---|
| Bilder (Standard) | `flux-2-klein-4b-fp8.safetensors`, `qwen_3_4b.safetensors`, `flux2-vae.safetensors` | [FLUX.2 Klein 4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B), [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) | Apache-2.0 |
| Bilder (Option `MODELL=dev`) | `flux2-dev-Q4_K_M.gguf`, `mistral_3_small_flux2_fp4_mixed.safetensors`, Knoten [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF) | [FLUX.2 dev](https://huggingface.co/black-forest-labs/FLUX.2-dev) | [FLUX Non-Commercial License](https://huggingface.co/black-forest-labs/FLUX.2-dev/blob/main/LICENSE.md), kommerzielle Nutzung nur mit Lizenz von BFL |
| Video | `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors`, `ltx-2.5-video-vae-bf16.safetensors`, `ltx-2.5-audio-vae-bf16.safetensors`, `ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors` | [Lightricks LTX-2.5](https://huggingface.co/Lightricks/LTX-2.5) | [LTX-2.x Community License](https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x) |
| Textencoder für Video | `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` | ComfyUI-Konvertierung von Gemma 4, z. B. [mcmonkey/swarm-models](https://huggingface.co/mcmonkey/swarm-models) | Gemma 4: Apache-2.0 laut [Hugging Face](https://huggingface.co/blog/gemma4) |

Platz für die Klein-4B-Modelle samt Video rund 49 GB. Die Lizenzseiten wurden am 09.10.2026 gelesen; maßgeblich ist immer die Originalseite. Die Codelizenz steht in `LICENSE` und gilt nur für die Skripte.

## Wenn etwas hakt

- `Port 8189 ist belegt`: das laufende ComfyUI zuerst selbst beenden.
- Abbruch wegen Speicher: andere Programme schließen und neu starten; fertige Teile werden übernommen. Bei einem Clipfehler rechnet `schritt3_clips.py` selbst eine kleinere Kachel (256); in unseren Läufen war das nie nötig.
- `ModuleNotFoundError: No module named 'lib'` kommt nur mit alten Fassungen des Pakets vor.
- Der Messwert `abstand_start` (erstes Clipbild gegen Standbild) lag bei uns zwischen 3,5 und 8,5. Erst über 20 gilt ein Clip als kaputt.

## Ordner

- `story/`: Geschichte, Figuren, Einstellungen.
- `runner/`: Selbstläufer und Einzelschritte (`schritt1` bis `schritt5`, `clips_einzeln.py`), Tests ohne GPU (`test_runner_ohne_gpu.py`).
- `workflows/`: API-Vorlagen für ComfyUI.
- `messung/beispiele/`: unsere Messwerte der drei Rechner.


## Teststand dieses Downloads

Am 10.10.2026 wurde der öffentlich heruntergeladene Commit `69f60db697c5b4930192c2b0d917621082cb88b7` auf dem GMKtec EVO-X2 (AMD Strix Halo, Ryzen AI Max+ 395) vollständig ausgeführt: 6 Figurenreferenzen, 36 neue Standbilder, 36 gültige Clips und Rohschnitt. Kein älteres Bild oder Video wurde für diesen Test wiederverwendet. Clip im Mittel: 430.0 s (381.9–447.4); gesamter Lauf: 4 h 49 min 46 s. Die getesteten generierenden Skripte und Story-Dateien bleiben in diesem Dokumentationsupdate unverändert. [Messung und Prüfgrenzen](GPU-RUN-NACHWEIS-20261010.md).

Verwendet wurden die vorhandene verifizierte ComfyUI-Installation und bereits vorhandene Modellgewichte. Eine vollständige Neuinstallation wurde nicht geprüft. Die Tabelle oben beschreibt die früheren Hardwareläufe; der neue EVO-X2-Test ist separat dokumentiert. Der neue Bandfilm verwendet zusätzlich gezielt erzeugte ChatGPT-Bildvorlagen und ist kein unveränderter Output dieses Downloads.

Die API-Verbindung ist lokal und ohne Login. Details: [Authentifizierung und Anfragen](AUTHENTIFIZIERUNG.md).
