# The Sisters of Messingbrunn

[Deutsch](README.md)

A steampunk short film made entirely on local hardware: 36 shots of 5 seconds each. A giant steam spider threatens the town of Messingbrunn, and the sisters Elara and Mira build an aether coil. This package creates the whole film from scratch on your own computer: characters, stills, clips and a rough cut. You only change text (see [PROMPTS-AENDERN.md](PROMPTS-AENDERN.md), German).

Included: scripts, story and workflows. Not included: model weights, finished images and the music from the video.

## What we did on three machines

Same scripts, same story, seed 11. Times from the measurement files (`messung/beispiele/drei-rechner.csv`).

| Machine | Memory | Images | Clip on average | Whole film from scratch |
|---|---|---|---|---|
| GMKtec EVO-X2 (AMD Strix Halo, Radeon 8060S) | shared memory | FLUX.2 Klein 4B | 436 s (397–466) | not measured from scratch; 36 clips: compute time 4 h 22 min, wall time with restarts 4 h 35 min |
| NVIDIA RTX 3080 Ti | 12 GB VRAM, 16 GB RAM | FLUX.2 Klein 4B, 13 s per image | 252 s (245–295) | 2 h 55 min |
| NVIDIA RTX 3090 Ti | 24 GB VRAM, 32 GB RAM | FLUX.2 Klein 4B, 8.5 s per image | 102 s (90–112) | 1 h 29 min |
| NVIDIA RTX 3090 Ti | 24 GB VRAM, 32 GB RAM | FLUX.2 dev (GGUF Q4_K_M), 242 s per image | 90 s (90–96) | 3 h 47 min |

Every run: 36 of 36 clips, no aborts, no retries. The RTX 3080 Ti is at the limit: VRAM peak 12,068 of 12,288 MiB, free RAM down to 3.9 GB. The FLUX.2 dev run left only 0.9 GB of 32 GB RAM free. Not tested: cards below 12 GB VRAM, less than 16 GB RAM, Linux, Mac.


## How to start

1. Install **ComfyUI** (tested: ComfyUI 0.38.0; the Windows portable build on NVIDIA, ComfyUI with ROCm for Windows on the EVO-X2).
2. Put the **models** from the table below into the ComfyUI folders. The package does not download anything itself.
3. **ffmpeg** and **ffprobe** must be on the path (`ffmpeg -version` must answer).
4. In a command prompt (adjust the paths):
   ```text
   set COMFYUI_DIR=C:\path\ComfyUI_windows_portable\ComfyUI
   set COMFYUI_PYTHON=C:\path\ComfyUI_windows_portable\python_embeded\python.exe
   START-SELBSTLAEUFER.cmd
   ```
   Optional before that: `set MODELL=dev` (FLUX.2 dev instead of Klein 4B) or `set GERAET=mypc` (name of the measurement file).
5. Wait. At the end you get `bilder\`, `clips\` and `film_roh.mp4` (no sound), and the measurements in `messung\<device>.jsonl`.

The runner starts its own ComfyUI on port 8189, a fresh one for every clip, with `--disable-pinned-memory`. Without that option LTX-2.5 gave us grey noise or aborted while loading. Port 8189 must be free; the runner never stops other programs. Close browsers, games and other AI tools first.

## Your own story

`story/figuren.json` describes the characters, `story/shots.json` the 36 shots (`bild` = image, `bewegung` = motion, `figuren` = characters). After a change, the next start only recomputes what is affected: a changed `bewegung` only the clip, a changed `bild` the still and the clip, a changed character her references and every shot she appears in. Old files move to `alt_...` folders.

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

- `story/`: story, characters, shots.
- `runner/`: runner and single steps (`schritt1` to `schritt5`, `clips_einzeln.py`), tests without GPU (`test_runner_ohne_gpu.py`).
- `workflows/`: API templates for ComfyUI.
- `messung/beispiele/`: our measurements from the three machines.


## Validation of this download

On 10 October 2026, the publicly downloaded commit `69f60db697c5b4930192c2b0d917621082cb88b7` was run completely on the GMKtec EVO-X2 (AMD Strix Halo, Ryzen AI Max+ 395): 6 character references, 36 new stills, 36 valid clips, and a rough cut. No previous image or video outputs were reused in this test. Mean clip time: 430.0 s (381.9–447.4); complete wall time: 4 h 49 min 46 s. The generating scripts and story files tested remain unchanged in this documentation update. [Measurements and validation limits](GPU-RUN-NACHWEIS-20261010.md).

The existing verified ComfyUI installation and already available model weights were used. A fresh installation has not been tested. The table above describes earlier hardware runs; the new EVO-X2 test is documented separately. The music short film also uses targeted new ChatGPT image references and is not an unchanged output of this download.

The API connection is local and uses no login. See [authentication and requests](AUTHENTIFIZIERUNG.md).
