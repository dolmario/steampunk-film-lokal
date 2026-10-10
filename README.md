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
- `02-REFERENZBILD-API-VORLAGE.json`: Standbild mit zwei Referenzen (Gesicht `10`–`14`, ganzer Körper `20`–`24`) → `CFGGuider` `90` → `SamplerCustomAdvanced` `95` → `VAEDecode` `96` → `SaveImage` `97`. Hinweis: Diese ältere Vorlage hat 1536 × 864; der Runner rechnet 1344 × 768. Sie bleibt unverändert liegen; die Runner-Werte stehen in den `-RUNNER-`-Vorlagen unten.
- `03-CLIP-API-VORLAGE.json`: Clip. Kern der Verbindungen:
  - `1` LoadImage → `2` ResizeImageMaskNode → `3` LTXVPreprocess (Startbild)
  - `4` CLIPLoader (Gemma) → `5`/`6` CLIPTextEncode → `10` LTXVConditioning (Port 0 positiv, Port 1 negativ)
  - `11` EmptyLTXVLatentVideo (640×360, 121) → `12` LTXVImgToVideoInplace (Strength 0.7) → `14` LTXVConcatAVLatent (mit Audiolatent `13`)
  - `18` LTXVDualCFGGuider + `17` ManualSigmas + `16` euler_ancestral → `19` SamplerCustomAdvanced → `20` LTXVSeparateAVLatent
  - `22` LTXVLatentUpsampler (Upscaler `21`) → `23` LTXVImgToVideoInplace (Strength 1.0) → `24` ConcatAV (Audio aus `20`, Port 1) → `29` SamplerCustomAdvanced → `30` Separate
  - `31` VAEDecodeTiled → `32` CreateVideo → `33` SaveVideo

**Welche Datei zu welchem Schritt gehört (so wie `runner/ablaeufe.py` sie baut):**

| Schritt | Vorlage | Quelle im Runner | Eingabe (zu ersetzen) | Modell / Sampler |
|---|---|---|---|---|
| Figurenreferenz, 1024 × 1024 | `01-FIGURENBLATT-API-VORLAGE.json` | `ablaeufe.klein(..., 1024, 1024)`, keine Referenzen | Node `4` Text | Klein 4B, 4 Schritte, CFG 1.0, euler, Seed 11 |
| Standbild Klein 4B, 1344 × 768 | `02-REFERENZBILD-KLEIN4-RUNNER-1344x768-API-VORLAGE.json` | `ablaeufe.klein(..., modell="klein4")` | Node `4` Text, `10` Gesicht, `20` Körper (Dateinamen aus dem ComfyUI-`input`-Ordner) | wie oben |
| Standbild FLUX.2 dev, 1344 × 768 | `02-REFERENZBILD-DEV-RUNNER-1344x768-API-VORLAGE.json` | `ablaeufe.dev(...)` | wie oben | GGUF Q4_K_M, 20 Schritte, FluxGuidance 4.0, `UnetLoaderGGUF` |
| Standbild 1536 × 864 (alt) | `02-REFERENZBILD-API-VORLAGE.json` | nicht mehr vom Runner benutzt | wie oben | wie Klein 4B |
| Clip | `03-CLIP-API-VORLAGE.json` | `ablaeufe.ltx_i2v(..., 5 s, Seed 11, tile 512)`; Werte stimmen mit dem Runner überein | Node `1` Startbild, `5` Bewegungstext | LTX-2.5 distilled, Werte siehe Tabelle oben |

Die Runner-Vorlagen haben je eine Figur (zwei Referenzen: Gesicht, Körper). Bei einer zweiten Figur im Shot hängt der Runner pro Referenz die vier Nodes `LoadImage` → `ImageScaleToTotalPixels` → `VAEEncode` → `ReferenceLatent` (Klein: positiv und negativ) an. `workflows/VORLAGEN-AUS-RUNNER.py` schreibt die beiden Runner-Vorlagen aus `ablaeufe.py` neu (nur Text, kein ComfyUI).

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

## Nachbauen: drei getestete Hardwareprofile

Startprozess, Runner und LTX-Werte sind in allen Profilen gleich. Es unterscheiden sich Runtime und die Modellauswahl.

| Profil | Speicher | Bildmodell | Runtime | Getestet |
|---|---|---|---|---|
| **AMD Strix Halo (EVO-X2)** | 64 GB gemeinsamer physischer Speicher (RAM und GPU-Speicher teilen sich dieselben 64 GB, es ist kein zusätzlicher VRAM) | Klein 4B | vorhandene ComfyUI-Installation 0.38.0 mit ROCm (PyTorch 2.9.1+rocm7.2.1) | ganzer Film, 4 h 49 min |
| **NVIDIA 12 GB VRAM + 16 GB RAM** (RTX 3080 Ti) | 12 GB VRAM, 16 GB RAM | Klein 4B | ComfyUI 0.38.0 Windows-Portable (NVIDIA) | ganzer Film, 2 h 55 min; VRAM-Spitze 12 068 von 12 288 MiB, also kein Spielraum |
| **NVIDIA 24 GB VRAM + 32 GB RAM** (RTX 3090 Ti) | 24 GB VRAM, 32 GB RAM | Klein 4B, optional dev | ComfyUI 0.38.0 Portable, Torch 2.14.0+cu130 | Klein: 1 h 29 min; dev: 3 h 47 min (dann nur noch 0,9 GB RAM frei) |

Nicht getestet und deshalb nicht zugesagt: weniger als 12 GB VRAM oder 16 GB RAM, dev auf 16 GB RAM, Linux, Mac, HDD statt SSD, eine frische Neuinstallation von ComfyUI/ROCm. Die Zeiten oben gelten für die jeweilige Maschine.

Was sich je Profil ändert:

- **Halo:** `COMFYUI_PYTHON` zeigt auf das Python der vorhandenen ROCm-ComfyUI-Umgebung (häufig ein `venv`), nicht auf `python_embeded`.
- **NVIDIA 12 GB / 24 GB:** `COMFYUI_PYTHON` ist `python_embeded\python.exe` der Portable-Fassung. Auf der 24-GB-Karte kannst du `set MODELL=dev` probieren; auf 12 GB bleibt es bei Klein 4B.
- **Modellpfade:** dieselben Dateinamen in allen Profilen (Tabelle „Modelle und Lizenzen“); nur der ComfyUI-Ordner, in dem sie liegen, ist ein anderer.

## Nachbauweg in sechs Schritten

1. **Entpacken.** Repository als ZIP laden oder klonen und in einen Ordner ohne Leerzeichen legen, z. B. `C:\steampunk-film`. Alle Ausgaben (`bilder\`, `clips\`, `film_roh.mp4`, `messung\`) landen darin.
2. **Umgebung.** ComfyUI (0.38.0) läuft schon oder wird nach der jeweiligen ComfyUI-Anleitung eingerichtet. In dem Python, das später den Runner startet, müssen NumPy und Pillow vorhanden sein; `ffmpeg` und `ffprobe` müssen im Pfad liegen. Der Custom-Node [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF) wird nur für `MODELL=dev` gebraucht.
3. **Modelle.** Die Dateien aus der Tabelle „Modelle und Lizenzen“ in die üblichen ComfyUI-Modellordner legen: `models\diffusion_models` (Klein, LTX-Transformer; für dev-GGUF `models\unet`), `models\text_encoders` (Qwen3-4B, Gemma, Mistral), `models\vae` (Flux2-VAE, LTX Video-/Audio-VAE) und `models\latent_upscale_models` (LTX-Upscaler). Das Paket lädt nichts selbst. Wenn ComfyUI einen Dateinamen nicht findet, bricht der Lauf beim Laden mit dem Namen ab.
4. **Pfadzeilen.** Zwei Zeilen setzen (Pfade anpassen):
   ```text
   set COMFYUI_DIR=C:\Pfad\zu\ComfyUI
   set COMFYUI_PYTHON=C:\Pfad\zu\python.exe
   ```
   `COMFYUI_DIR` ist der Ordner mit `main.py`. Optional `set GERAET=meinpc` (Name der Messdatei) und `set MODELL=dev`.
5. **Starten.** `START-SELBSTLAEUFER.cmd` im Repository-Ordner ausführen, oder direkt `python runner/selbstlaeufer.py --geraet meinpc --comfyui <ComfyUI-Ordner> --modell klein4 --seed 11`. Der Lauf macht der Reihe nach Figurenreferenzen (6), Standbilder (36), Clips (36, je Clip ein frisches ComfyUI) und den Rohschnitt. Ist er unterbrochen, setzt ein neuer Start bei den fehlenden Teilen fort.
6. **Ergebnis.** `bilder\figuren\`, `bilder\standbilder\`, `clips\shot_NN.mp4` und `film_roh.mp4`. Zum Ausprobieren vorab nur einen Shot: `python runner/schritt2_standbilder.py --geraet meinpc --shots 12` und `python runner/schritt3_clips.py --geraet meinpc --shots 12` (ComfyUI muss dafür auf Port 8189 laufen).

Wer die Graphen lieber selbst in ComfyUI-API-Form abschickt: die Vorlagen in `workflows/` (Tabelle oben) sind dieselben Graphen, die der Runner schickt.

## Ausführlicher Start

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

- `Port 8189 ist belegt`: ein anderes ComfyUI (oder ein hängengebliebener Python-Prozess) hört dort. In dem Fenster, in dem es läuft, mit Strg+C beenden, dann neu starten. Der Selbstläufer beendet nur sein eigenes ComfyUI.
- Clip ist graues Rauschen oder ComfyUI bricht beim Laden ab: ComfyUI muss mit `--disable-pinned-memory` laufen. Der Selbstläufer und `clips_einzeln.py` setzen das selbst; wer ComfyUI von Hand startet, muss es angeben.
- `ModuleNotFoundError: No module named 'lib'` oder `'ablaeufe'`: die Skripte tragen ihren Ordner selbst in `sys.path` ein. Kommt der Fehler trotzdem (eigener Aufruf eines Skripts aus anderem Python-Setup, z. B. bei ComfyUI Portable), in `python_embeded\python313._pth` eine Zeile mit dem Pfad des Ordners `runner` ergänzen. Stehen dort mehrere Runner-Ordner, gewinnt der erste.
- Abbruch wegen Speicher: andere Programme schließen und neu starten; fertige Teile werden übernommen. Bei einem Clipfehler rechnet `schritt3_clips.py` selbst eine kleinere Kachel (256); in unseren Läufen war das nie nötig.
- `ffmpeg`/`ffprobe` nicht gefunden: im Pfad der Eingabeaufforderung fehlt der ffmpeg-Ordner.
- `START-SELBSTLAEUFER.cmd` benennt die Messdatei nach dem Rechnernamen; `set GERAET=meinpc` vorher setzt einen eigenen Namen.
- Der Messwert `abstand_start` (erstes Clipbild gegen Standbild) lag bei uns zwischen 3,5 und 8,5. Erst über 20 gilt ein Clip als kaputt.

## Ordner

- `story/`: Beispielgeschichte, Figuren, Einstellungen.
- `runner/`: Selbstläufer und Einzelschritte (`schritt1` bis `schritt5`, `clips_einzeln.py`), Tests ohne GPU (`test_runner_ohne_gpu.py`).
- `workflows/`: API-Vorlagen für ComfyUI.
- `messung/beispiele/`: Messwerte der Läufe.

Die API-Verbindung ist lokal und ohne Login: [AUTHENTIFIZIERUNG.md](AUTHENTIFIZIERUNG.md).
