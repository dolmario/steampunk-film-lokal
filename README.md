# Steampunk-Film lokal: Bilder und Clips mit FLUX.2 Klein und LTX-2.5

[English](README.en.md)

Dieses Repository zeigt einen lokal ausführbaren Ablauf von der Figurenbeschreibung bis zum Rohschnitt:

1. Figurenreferenzen mit FLUX.2 Klein 4B (optional FLUX.2 dev),
2. Standbilder pro Einstellung, die diese Referenzen nutzen,
3. 5-Sekunden-Clips mit LTX-2.5 aus jedem Standbild,
4. Rohschnitt `film_roh.mp4` (ohne Ton) per ffmpeg.

Als **Beispiel** liegt eine kleine Geschichte bei („Messingbrunn“: eine Dampf-Spinne, die Schwestern Elara und Mira, 36 Einstellungen). Sie dient nur zum Ausprobieren; du ersetzt sie durch deine eigene (siehe [PROMPTS-AENDERN.md](PROMPTS-AENDERN.md)).

## Zwei Dinge, die nicht dasselbe sind

| | Dieses Repository (GitHub-Lauf) | Musikvideo „Sickheadz – lost All I've Loved“ (Tom Bartelt / Sickheadz) |
|---|---|---|
| Inhalt | Beispielablauf: Klein, optional dev, LTX-2.5, Rohschnitt | fertiger Musikfilm, später geschnitten |
| Bildquellen | nur das, was die Workflows hier erzeugen | zusätzlich GPT-Bildvorlagen für gleichbleibende Figuren |
| Ton | keiner (stummer Rohschnitt) | Bandtrack, unverändert in Länge und Tempo; keine Erzählerin |
| im Download | Skripte, Story, Workflows, Messdaten | nicht enthalten (Bandtrack und GPT-Bilder sind nicht im Download) |

Der Lauf aus diesem Repository erzeugt also einen Rohschnitt aus dem Beispiel-Ablauf. Der Musikfilm ist ein eigener Schnitt mit eigenem Bildmaterial.

## Was tatsächlich eingestellt ist

Alles steht in `runner/ablaeufe.py`; die Werte hier sind von dort übernommen.

**Standbilder (FLUX.2 Klein 4B)**

| Einstellung | Wert |
|---|---|
| Größe | 1344 × 768 |
| Seed | 11 |
| Schritte (Flux2Scheduler) | 4 |
| CFG (CFGGuider) | 1.0 |
| Sampler | euler |
| Referenzen | je Referenzbild: LoadImage → ImageScaleToTotalPixels (1.0 MP) → VAEEncode → ReferenceLatent (positiv und negativ verkettet) |

Mit `MODELL=dev` (FLUX.2 dev, GGUF Q4_K_M): 20 Schritte, FluxGuidance 4.0, sonst gleiche Referenzkette.

**Clips (LTX-2.5 distilled, Bild-zu-Video)**

| Einstellung | Wert |
|---|---|
| Länge | 5 s, 24 fps, 121 Bilder |
| Erste Stufe | 640 × 360 Latent, Startbild mit Strength 0.7, Sigmas `1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0` |
| Hochskalierung | Latent-Upscaler ×2 |
| Zweite Stufe | Startbild erneut mit Strength 1.0, Sigmas `0.85, 0.7250, 0.4219, 0.0` |
| Sampler | euler_ancestral, Seed 11 |
| Decode | VAEDecodeTiled, tile_size 512 (Überlappung 64, zeitlich 64/16) |
| Ausgabe | mp4 (h264) |

## Der Workflow zum Herunterladen

In `workflows/` liegen die ComfyUI-API-Vorlagen. Dort stehen die exakten Node-Verbindungen (`["Node-ID", Ausgabe-Port]`):

- `01-FIGURENBLATT-API-VORLAGE.json`: Figurenreferenz.
- `02-REFERENZBILD-API-VORLAGE.json`: Standbild mit zwei Referenzen (Gesicht `10`–`14`, ganzer Körper `20`–`24`) → `CFGGuider` `90` → `SamplerCustomAdvanced` `95` → `VAEDecode` `96` → `SaveImage` `97`. Hinweis: Diese Vorlage hat 1536 × 864; der Runner selbst rechnet 1344 × 768.
- `03-CLIP-API-VORLAGE.json`: Clip. Kern der Verbindungen:
  - `1` LoadImage → `2` ResizeImageMaskNode → `3` LTXVPreprocess (Startbild)
  - `4` CLIPLoader (Gemma) → `5`/`6` CLIPTextEncode → `10` LTXVConditioning (Port 0 positiv, Port 1 negativ)
  - `11` EmptyLTXVLatentVideo (640×360, 121) → `12` LTXVImgToVideoInplace (Strength 0.7) → `14` LTXVConcatAVLatent (mit Audiolatent `13`)
  - `18` LTXVDualCFGGuider + `17` ManualSigmas + `16` euler_ancestral → `19` SamplerCustomAdvanced → `20` LTXVSeparateAVLatent
  - `22` LTXVLatentUpsampler (Upscaler `21`) → `23` LTXVImgToVideoInplace (Strength 1.0) → `24` ConcatAV (Audio aus `20`, Port 1) → `29` SamplerCustomAdvanced → `30` Separate
  - `31` VAEDecodeTiled → `32` CreateVideo → `33` SaveVideo

In den Vorlagen sind `REPLACE...`-Platzhalter für Bild und Prompt; im ComfyUI-API-Format kannst du sie per `POST /prompt` abschicken (Ablauf in [AUTHENTIFIZIERUNG.md](AUTHENTIFIZIERUNG.md)).

## Gemessene Läufe

Gleiche Skripte, gleiche Geschichte, Seed 11. Zeiten aus `messung/beispiele/`.

| Rechner | Speicher | Bilder | Clip im Mittel | Ganzer Film von null |
|---|---|---|---|---|
| GMKtec EVO-X2 (AMD Strix Halo, Ryzen AI Max+ 395, Radeon 8060S), Commit `69f60db` vom 10.10.2026 | gemeinsamer Speicher | FLUX.2 Klein 4B | 430 s (381,9–447,4) | 4 h 49 min 46 s (6 Referenzen, 36 neue Standbilder, 36 gültige Clips, Rohschnitt, 0 Wiederholungen) |
| GMKtec EVO-X2, früherer Lauf | gemeinsamer Speicher | FLUX.2 Klein 4B | 436 s (397–466) | nicht von null gemessen; 36 Clips: Rechenzeit 4 h 22 min, Laufzeit mit Neustarts 4 h 35 min |
| NVIDIA RTX 3080 Ti | 12 GB VRAM, 16 GB RAM | FLUX.2 Klein 4B, 13 s je Bild | 252 s (245–295) | 2 h 55 min |
| NVIDIA RTX 3090 Ti | 24 GB VRAM, 32 GB RAM | FLUX.2 Klein 4B, 8,5 s je Bild | 102 s (90–112) | 1 h 29 min |
| NVIDIA RTX 3090 Ti | 24 GB VRAM, 32 GB RAM | FLUX.2 dev (GGUF Q4_K_M), 242 s je Bild | 90 s (90–96) | 3 h 47 min |

Der EVO-Komplettlauf vom 10.10.2026 nutzte die vorhandene ComfyUI-Installation und vorhandene Modelle (keine saubere Neuinstallation). Details: [GPU-RUN-NACHWEIS-20261010.md](GPU-RUN-NACHWEIS-20261010.md).

Speicher: Die RTX 3080 Ti lief mit VRAM-Spitze 12 068 von 12 288 MiB und minimal 3,9 GB freiem RAM. Der dev-Lauf ließ auf 32 GB RAM 0,9 GB frei. Karten unter 12 GB VRAM, unter 16 GB RAM, Linux und Mac wurden nicht getestet.

## So startest du

1. **ComfyUI** installieren (verwendet: ComfyUI 0.38.0; auf NVIDIA die Windows-Portable-Fassung, auf dem EVO-X2 ComfyUI mit ROCm für Windows).
2. **Modelle** aus der Tabelle unten in die ComfyUI-Ordner legen. Das Paket lädt nichts selbst herunter.
3. **ffmpeg** und **ffprobe** im Pfad (`ffmpeg -version` muss antworten).
4. In der Eingabeaufforderung (Pfade anpassen):
   ```text
   set COMFYUI_DIR=C:\Pfad\ComfyUI_windows_portable\ComfyUI
   set COMFYUI_PYTHON=C:\Pfad\ComfyUI_windows_portable\python_embeded\python.exe
   START-SELBSTLAEUFER.cmd
   ```
   Optional vorher: `set MODELL=dev` (FLUX.2 dev statt Klein 4B) oder `set GERAET=meinpc` (Name der Messdatei).
   Direkter Aufruf wie im EVO-Lauf:
   ```text
   python runner/selbstlaeufer.py --geraet evo --comfyui <ComfyUI-Ordner> --modell klein4 --seed 11
   ```
5. Am Ende liegen `bilder\`, `clips\` und `film_roh.mp4` (ohne Ton) im Ordner, die Messwerte in `messung\<Gerät>.jsonl`.

Der Selbstläufer startet sein eigenes ComfyUI auf Port 8189, für jeden Clip frisch und mit `--disable-pinned-memory`. Ohne diese Option lieferte LTX-2.5 bei uns graues Rauschen oder brach beim Laden ab. Port 8189 muss frei sein; der Selbstläufer beendet keine fremden Programme. Browser, Spiele und andere KI-Programme vorher schließen.

## Eigene Geschichte

`story/figuren.json` beschreibt die Figuren, `story/shots.json` die Einstellungen (`bild`, `bewegung`, `figuren`). Nach einer Änderung rechnet der nächste Start nur das Betroffene neu: geänderte `bewegung` nur den Clip, geändertes `bild` Standbild und Clip, eine geänderte Figur ihre Referenzen und alle Einstellungen mit ihr. Alte Dateien wandern in `alt_...`-Ordner. Details: [PROMPTS-AENDERN.md](PROMPTS-AENDERN.md).

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

- `story/`: Beispielgeschichte, Figuren, Einstellungen.
- `runner/`: Selbstläufer und Einzelschritte (`schritt1` bis `schritt5`, `clips_einzeln.py`), Tests ohne GPU (`test_runner_ohne_gpu.py`).
- `workflows/`: API-Vorlagen für ComfyUI.
- `messung/beispiele/`: Messwerte der Läufe.

Die API-Verbindung ist lokal und ohne Login: [AUTHENTIFIZIERUNG.md](AUTHENTIFIZIERUNG.md).
