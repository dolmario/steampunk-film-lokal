# Local steampunk film: images and clips with FLUX.2 Klein and LTX-2.5

[Deutsch](README.md)

This repository shows a locally runnable pipeline from character descriptions to a rough cut:

1. character references with FLUX.2 Klein 4B (optionally FLUX.2 dev),
2. one still per shot that uses those references,
3. 5-second clips with LTX-2.5 from each still,
4. rough cut `film_roh.mp4` (no sound) via ffmpeg.

A small **example** story is included ("Messingbrunn": a steam spider, the sisters Elara and Mira, 36 shots). It is there to try things out; replace it with your own (see [PROMPTS-AENDERN.md](PROMPTS-AENDERN.md), German).

## Two things that are not the same

| | This repository (GitHub run) | Music video "Sickheadz – lost All I've Loved" (Tom Bartelt / Sickheadz) |
|---|---|---|
| Content | Example pipeline: Klein, optional dev, LTX-2.5, rough cut | finished music film, cut later |
| Image sources | only what the workflows here generate | additionally GPT image templates for consistent characters |
| Sound | none (silent rough cut) | band track, unchanged in length and tempo; no narrator |
| In the download | scripts, story, workflows, measurements | not included (band track and GPT images are not in the download) |

So running this repository produces a rough cut from the example pipeline. The music film is a separate edit with its own image material.

## Actual settings

Everything is in `runner/ablaeufe.py`; the values below are taken from there.

**Stills (FLUX.2 Klein 4B)**

| Setting | Value |
|---|---|
| Size | 1344 × 768 |
| Seed | 11 |
| Steps (Flux2Scheduler) | 4 |
| CFG (CFGGuider) | 1.0 |
| Sampler | euler |
| References | per reference image: LoadImage → ImageScaleToTotalPixels (1.0 MP) → VAEEncode → ReferenceLatent (chained on positive and negative) |

With `MODELL=dev` (FLUX.2 dev, GGUF Q4_K_M): 20 steps, FluxGuidance 4.0, same reference chain otherwise.

**Clips (LTX-2.5 distilled, image-to-video)**

| Setting | Value |
|---|---|
| Length | 5 s, 24 fps, 121 frames |
| First stage | 640 × 360 latent, start image with strength 0.7, sigmas `1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0` |
| Upscale | latent upscaler ×2 |
| Second stage | start image again with strength 1.0, sigmas `0.85, 0.7250, 0.4219, 0.0` |
| Sampler | euler_ancestral, seed 11 |
| Decode | VAEDecodeTiled, tile_size 512 (overlap 64, temporal 64/16) |
| Output | mp4 (h264) |

## The downloadable workflows

`workflows/` holds the ComfyUI API templates with the exact node connections (`["node id", output port]`):

- `01-FIGURENBLATT-API-VORLAGE.json`: character reference.
- `02-REFERENZBILD-API-VORLAGE.json`: still with two references (face `10`–`14`, full body `20`–`24`) → `CFGGuider` `90` → `SamplerCustomAdvanced` `95` → `VAEDecode` `96` → `SaveImage` `97`. Note: this older template uses 1536 × 864; the runner renders 1344 × 768. It stays unchanged. The runner values are in two additional templates, one reference-pair (face, body) each: `02-REFERENZBILD-KLEIN4-RUNNER-1344x768-API-VORLAGE.json` (Klein 4B, 4 steps, CFG 1.0, euler, seed 11) and `02-REFERENZBILD-DEV-RUNNER-1344x768-API-VORLAGE.json` (FLUX.2 dev GGUF Q4_K_M, 20 steps, FluxGuidance 4.0). Inputs to replace: node `4` (text), `10` (face image), `20` (body image). `workflows/VORLAGEN-AUS-RUNNER.py` regenerates both from `runner/ablaeufe.py` (text only). `03-CLIP-API-VORLAGE.json` already matches the runner (5 s, seed 11, tile 512); inputs: node `1` (start image), `5` (motion text).
- `03-CLIP-API-VORLAGE.json`: clip. Core connections:
  - `1` LoadImage → `2` ResizeImageMaskNode → `3` LTXVPreprocess (start image)
  - `4` CLIPLoader (Gemma) → `5`/`6` CLIPTextEncode → `10` LTXVConditioning (port 0 positive, port 1 negative)
  - `11` EmptyLTXVLatentVideo (640×360, 121) → `12` LTXVImgToVideoInplace (strength 0.7) → `14` LTXVConcatAVLatent (with audio latent `13`)
  - `18` LTXVDualCFGGuider + `17` ManualSigmas + `16` euler_ancestral → `19` SamplerCustomAdvanced → `20` LTXVSeparateAVLatent
  - `22` LTXVLatentUpsampler (upscaler `21`) → `23` LTXVImgToVideoInplace (strength 1.0) → `24` ConcatAV (audio from `20`, port 1) → `29` SamplerCustomAdvanced → `30` Separate
  - `31` VAEDecodeTiled → `32` CreateVideo → `33` SaveVideo

The templates contain `REPLACE...` placeholders for image and prompt; in ComfyUI API format you can submit them with `POST /prompt` (flow in [AUTHENTIFIZIERUNG.md](AUTHENTIFIZIERUNG.md), German).

## Measured runs

Same scripts, same story, seed 11. Times from `messung/beispiele/`.

| Machine | Memory | Images | Clip on average | Whole film from scratch |
|---|---|---|---|---|
| GMKtec EVO-X2 (AMD Strix Halo, Ryzen AI Max+ 395, Radeon 8060S), commit `69f60db` of 10 Oct 2026 | shared memory | FLUX.2 Klein 4B | 430 s (381.9–447.4) | 4 h 49 min 46 s (6 references, 36 new stills, 36 valid clips, rough cut, 0 retries) |
| GMKtec EVO-X2, earlier run | shared memory | FLUX.2 Klein 4B | 436 s (397–466) | not measured from scratch; 36 clips: compute time 4 h 22 min, wall time with restarts 4 h 35 min |
| NVIDIA RTX 3080 Ti | 12 GB VRAM, 16 GB RAM | FLUX.2 Klein 4B, 13 s per image | 252 s (245–295) | 2 h 55 min |
| NVIDIA RTX 3090 Ti | 24 GB VRAM, 32 GB RAM | FLUX.2 Klein 4B, 8.5 s per image | 102 s (90–112) | 1 h 29 min |
| NVIDIA RTX 3090 Ti | 24 GB VRAM, 32 GB RAM | FLUX.2 dev (GGUF Q4_K_M), 242 s per image | 90 s (90–96) | 3 h 47 min |

The EVO full run of 10 Oct 2026 used the existing ComfyUI installation and existing models (no clean reinstall). Details: [GPU-RUN-NACHWEIS-20261010.md](GPU-RUN-NACHWEIS-20261010.md) (German).

Memory: the RTX 3080 Ti ran with a VRAM peak of 12,068 of 12,288 MiB and a minimum of 3.9 GB free RAM. The dev run left 0.9 GB of 32 GB RAM free. Cards below 12 GB VRAM, less than 16 GB RAM, Linux and Mac were not tested.

## Rebuilding: three tested hardware profiles

Start process, runner and LTX values are identical; runtime and model location differ.

| Profile | Memory | Image model | Runtime | Tested |
|---|---|---|---|---|
| AMD Strix Halo (EVO-X2) | 64 GB unified memory (one shared pool, not extra VRAM) | Klein 4B | existing ComfyUI 0.38.0 with ROCm | full film, 4 h 49 min |
| NVIDIA 12 GB VRAM + 16 GB RAM (RTX 3080 Ti) | 12 GB / 16 GB | Klein 4B | ComfyUI 0.38.0 Windows portable | full film, 2 h 55 min, VRAM peak 12,068 of 12,288 MiB |
| NVIDIA 24 GB VRAM + 32 GB RAM (RTX 3090 Ti) | 24 GB / 32 GB | Klein 4B, optional dev | ComfyUI 0.38.0 portable | Klein 1 h 29 min; dev 3 h 47 min (0.9 GB RAM left) |

Not tested, so not promised: less than 12 GB VRAM or 16 GB RAM, dev on 16 GB RAM, Linux, Mac, HDD, a fresh ROCm/ComfyUI installation.

Steps: (1) unpack into a folder without spaces; (2) have ComfyUI running in the profile's runtime, NumPy and Pillow in the Python that starts the runner, `ffmpeg`/`ffprobe` in PATH (ComfyUI-GGUF only for `MODELL=dev`); (3) put the model files from the table below into the ComfyUI model folders (`diffusion_models`, `text_encoders`, `vae`, `latent_upscale_models`, `unet` for GGUF); (4) set `COMFYUI_DIR` (folder with `main.py`) and `COMFYUI_PYTHON`; (5) run `START-SELBSTLAEUFER.cmd`; (6) find `bilder\`, `clips\` and `film_roh.mp4` in the folder. For a single shot first: `python runner/schritt2_standbilder.py --geraet mypc --shots 12`, then `schritt3_clips.py` the same way (ComfyUI on port 8189).

Common problems: port 8189 busy → close the other ComfyUI with Ctrl+C; grey noise or load abort → ComfyUI needs `--disable-pinned-memory` (the runner sets it); `ModuleNotFoundError` for `lib`/`ablaeufe` → the scripts add their own folder to `sys.path`, otherwise add the `runner` folder as a line in `python_embeded\python313._pth` (the first runner folder listed wins).

## How to start

1. Install **ComfyUI** (used: ComfyUI 0.38.0; the Windows portable build on NVIDIA, ComfyUI with ROCm for Windows on the EVO-X2).
2. Put the **models** from the table below into the ComfyUI folders. The package does not download anything itself.
3. **ffmpeg** and **ffprobe** on the path (`ffmpeg -version` must answer).
4. In a command prompt (adjust the paths):
   ```text
   set COMFYUI_DIR=C:\path\ComfyUI_windows_portable\ComfyUI
   set COMFYUI_PYTHON=C:\path\ComfyUI_windows_portable\python_embeded\python.exe
   START-SELBSTLAEUFER.cmd
   ```
   Optional before that: `set MODELL=dev` (FLUX.2 dev instead of Klein 4B) or `set GERAET=mypc` (name of the measurement file).
   Direct call as in the EVO run:
   ```text
   python runner/selbstlaeufer.py --geraet evo --comfyui <ComfyUI folder> --modell klein4 --seed 11
   ```
5. At the end you get `bilder\`, `clips\` and `film_roh.mp4` (no sound), and the measurements in `messung\<device>.jsonl`.

The runner starts its own ComfyUI on port 8189, a fresh one for every clip, with `--disable-pinned-memory`. Without that option LTX-2.5 gave us grey noise or aborted while loading. Port 8189 must be free; the runner never stops other programs. Close browsers, games and other AI tools first.

## Your own story

`story/figuren.json` describes the characters, `story/shots.json` the shots (`bild` = image, `bewegung` = motion, `figuren` = characters). After a change, the next start only recomputes what is affected: a changed `bewegung` only the clip, a changed `bild` the still and the clip, a changed character her references and every shot she appears in. Old files move to `alt_...` folders.

## Models and licences

File names are in `runner/ablaeufe.py`.

| Task | Files | Source | Licence according to the source |
|---|---|---|---|
| Images (default) | `flux-2-klein-4b-fp8.safetensors`, `qwen_3_4b.safetensors`, `flux2-vae.safetensors` | [FLUX.2 Klein 4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B), [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) | Apache-2.0 |
| Images (option `MODELL=dev`) | `flux2-dev-Q4_K_M.gguf`, `mistral_3_small_flux2_fp4_mixed.safetensors`, node [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF) | [FLUX.2 dev](https://huggingface.co/black-forest-labs/FLUX.2-dev) | [FLUX Non-Commercial License](https://huggingface.co/black-forest-labs/FLUX.2-dev/blob/main/LICENSE.md), commercial use only with a licence from BFL |
| Video | `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors`, `ltx-2.5-video-vae-bf16.safetensors`, `ltx-2.5-audio-vae-bf16.safetensors`, `ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors` | [Lightricks LTX-2.5](https://huggingface.co/Lightricks/LTX-2.5) | [LTX-2.x Community License](https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x) |
| Text encoder for video | `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` | ComfyUI conversion of Gemma 4, e.g. [mcmonkey/swarm-models](https://huggingface.co/mcmonkey/swarm-models) | Gemma 4: Apache-2.0 according to [Hugging Face](https://huggingface.co/blog/gemma4) |

Klein 4B plus the video models need about 49 GB of disk space. The licence pages were read on 9 October 2026; the original page always applies. The code licence is in `LICENSE` and covers the scripts only.

## Troubleshooting

- `Port 8189 ist belegt` (port in use): stop the running ComfyUI yourself first.
- Out of memory: close other programs and start again; finished parts are reused. If a clip fails, `schritt3_clips.py` retries with a smaller tile (256); our runs never needed it.
- `ModuleNotFoundError: No module named 'lib'` only happens with old versions of this package.
- The value `abstand_start` (first clip frame against the still) was between 3.5 and 8.5 in our runs. Only above 20 is a clip considered broken.

## Folders

- `story/`: example story, characters, shots.
- `runner/`: runner and single steps (`schritt1` to `schritt5`, `clips_einzeln.py`), tests without GPU (`test_runner_ohne_gpu.py`).
- `workflows/`: API templates for ComfyUI.
- `messung/beispiele/`: measurements from the runs.

The API connection is local and uses no login: [AUTHENTIFIZIERUNG.md](AUTHENTIFIZIERUNG.md).
