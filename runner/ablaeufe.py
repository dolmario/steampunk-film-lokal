"""ComfyUI-API-Graphen: FLUX.2 Klein oder FLUX.2 dev mit Referenzbildern und LTX-2.5 Bild-zu-Video."""

NEGATIV_LTX = "pc game, console game, video game, cartoon, childish, ugly, deformed face, extra limbs, blurry"
KLEIN_MODELLE = {
    "klein4": ("flux-2-klein-4b-fp8.safetensors", "qwen_3_4b.safetensors"),
    "klein9": ("flux-2-klein-9b-fp8.safetensors", "qwen_3_8b_fp8mixed.safetensors"),
}


def dev(prompt, refs, breite, hoehe, seed, prefix):
    """FLUX.2 dev (GGUF Q4_K_M, braucht den Knoten UnetLoaderGGUF), 20 Schritte, FluxGuidance 4.0, Referenzen wie bei Klein."""
    g = {
        "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "flux2-dev-Q4_K_M.gguf"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "mistral_3_small_flux2_fp4_mixed.safetensors", "type": "flux2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
    }
    pos = ["4", 0]
    for n, name in enumerate(refs):
        b = 10 + n * 10
        g[str(b)] = {"class_type": "LoadImage", "inputs": {"image": name}}
        g[str(b + 1)] = {"class_type": "ImageScaleToTotalPixels", "inputs": {
            "image": [str(b), 0], "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 32}}
        g[str(b + 2)] = {"class_type": "VAEEncode", "inputs": {"pixels": [str(b + 1), 0], "vae": ["3", 0]}}
        g[str(b + 3)] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": pos, "latent": [str(b + 2), 0]}}
        pos = [str(b + 3), 0]
    g.update({
        "89": {"class_type": "FluxGuidance", "inputs": {"conditioning": pos, "guidance": 4.0}},
        "90": {"class_type": "BasicGuider", "inputs": {"model": ["1", 0], "conditioning": ["89", 0]}},
        "91": {"class_type": "Flux2Scheduler", "inputs": {"steps": 20, "width": breite, "height": hoehe}},
        "92": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": breite, "height": hoehe, "batch_size": 1}},
        "93": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "94": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "95": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["94", 0], "guider": ["90", 0], "sampler": ["93", 0], "sigmas": ["91", 0], "latent_image": ["92", 0]}},
        "96": {"class_type": "VAEDecode", "inputs": {"samples": ["95", 0], "vae": ["3", 0]}},
        "97": {"class_type": "SaveImage", "inputs": {"images": ["96", 0], "filename_prefix": prefix}},
    })
    return g


def klein(prompt, refs, breite, hoehe, seed, prefix, modell="klein4"):
    """Text-zu-Bild, mit `refs` (hochgeladene Dateinamen) als ReferenceLatent-Kette."""
    if modell == "dev":
        return dev(prompt, refs, breite, hoehe, seed, prefix)
    unet, clip = KLEIN_MODELLE[modell]
    g = {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": unet, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": clip, "type": "flux2", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
        "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "5": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
    }
    pos, neg = ["4", 0], ["5", 0]
    for n, name in enumerate(refs):
        b = 10 + n * 10
        g[str(b)] = {"class_type": "LoadImage", "inputs": {"image": name}}
        g[str(b + 1)] = {"class_type": "ImageScaleToTotalPixels", "inputs": {
            "image": [str(b), 0], "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 32}}
        g[str(b + 2)] = {"class_type": "VAEEncode", "inputs": {"pixels": [str(b + 1), 0], "vae": ["3", 0]}}
        g[str(b + 3)] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": pos, "latent": [str(b + 2), 0]}}
        g[str(b + 4)] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": neg, "latent": [str(b + 2), 0]}}
        pos, neg = [str(b + 3), 0], [str(b + 4), 0]
    g.update({
        "90": {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": pos, "negative": neg, "cfg": 1.0}},
        "91": {"class_type": "Flux2Scheduler", "inputs": {"steps": 4, "width": breite, "height": hoehe}},
        "92": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": breite, "height": hoehe, "batch_size": 1}},
        "93": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
        "94": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "95": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["94", 0], "guider": ["90", 0], "sampler": ["93", 0], "sigmas": ["91", 0], "latent_image": ["92", 0]}},
        "96": {"class_type": "VAEDecode", "inputs": {"samples": ["95", 0], "vae": ["3", 0]}},
        "97": {"class_type": "SaveImage", "inputs": {"images": ["96", 0], "filename_prefix": prefix}},
    })
    return g


def ltx_i2v(bild, prompt, sekunden, seed, prefix, tile=512, start_staerke=0.7):
    """LTX-2.5 distilled, zwei Stufen (360p-Latent, x2-Upscaler, Verfeinerung), Ton im selben Lauf."""
    laenge = int(sekunden * 24) + 1
    return {
        "1": {"class_type": "LoadImage", "inputs": {"image": bild}},
        "2": {"class_type": "ResizeImageMaskNode", "inputs": {
            "input": ["1", 0], "resize_type": "scale longer dimension",
            "resize_type.longer_size": 1536, "scale_method": "lanczos"}},
        "3": {"class_type": "LTXVPreprocess", "inputs": {"image": ["2", 0], "img_compression": 18}},
        "4": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors", "type": "ltxv", "device": "default"}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 0]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": NEGATIV_LTX, "clip": ["4", 0]}},
        "7": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors", "weight_dtype": "default"}},
        "8": {"class_type": "VAELoader", "inputs": {"vae_name": "ltx-2.5-video-vae-bf16.safetensors"}},
        "9": {"class_type": "VAELoader", "inputs": {"vae_name": "ltx-2.5-audio-vae-bf16.safetensors"}},
        "10": {"class_type": "LTXVConditioning", "inputs": {"positive": ["5", 0], "negative": ["6", 0], "frame_rate": 24.0}},
        "11": {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": 640, "height": 360, "length": laenge, "batch_size": 1}},
        "12": {"class_type": "LTXVImgToVideoInplace", "inputs": {
            "vae": ["8", 0], "image": ["3", 0], "latent": ["11", 0], "strength": start_staerke, "bypass": False}},
        "13": {"class_type": "LTXVEmptyLatentAudio", "inputs": {
            "audio_vae": ["9", 0], "frames_number": laenge, "frame_rate": 24, "batch_size": 1}},
        "14": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["12", 0], "audio_latent": ["13", 0]}},
        "15": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "16": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}},
        "17": {"class_type": "ManualSigmas", "inputs": {
            "sigmas": "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"}},
        "18": {"class_type": "LTXVDualCFGGuider", "inputs": {
            "model": ["7", 0], "positive": ["10", 0], "negative": ["10", 1], "video_cfg": 1.0, "audio_cfg": 1.0}},
        "19": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["15", 0], "guider": ["18", 0], "sampler": ["16", 0], "sigmas": ["17", 0], "latent_image": ["14", 0]}},
        "20": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["19", 0]}},
        "21": {"class_type": "LatentUpscaleModelLoader", "inputs": {
            "model_name": "ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors"}},
        "22": {"class_type": "LTXVLatentUpsampler", "inputs": {"samples": ["20", 0], "upscale_model": ["21", 0], "vae": ["8", 0]}},
        "23": {"class_type": "LTXVImgToVideoInplace", "inputs": {
            "vae": ["8", 0], "image": ["3", 0], "latent": ["22", 0], "strength": 1.0, "bypass": False}},
        "24": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["23", 0], "audio_latent": ["20", 1]}},
        "25": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "26": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}},
        "27": {"class_type": "ManualSigmas", "inputs": {"sigmas": "0.85, 0.7250, 0.4219, 0.0"}},
        "28": {"class_type": "LTXVDualCFGGuider", "inputs": {
            "model": ["7", 0], "positive": ["10", 0], "negative": ["10", 1], "video_cfg": 1.0, "audio_cfg": 1.0}},
        "29": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["25", 0], "guider": ["28", 0], "sampler": ["26", 0], "sigmas": ["27", 0], "latent_image": ["24", 0]}},
        "30": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["29", 0]}},
        "31": {"class_type": "VAEDecodeTiled", "inputs": {
            "samples": ["30", 0], "vae": ["8", 0], "tile_size": tile, "overlap": 64, "temporal_size": 64, "temporal_overlap": 16}},
        "32": {"class_type": "CreateVideo", "inputs": {
            "images": ["31", 0], "fps": 24.0, "bit_depth": 8, "color_space": "sRGB", "codec": "h264"}},
        "33": {"class_type": "SaveVideo", "inputs": {"video": ["32", 0], "filename_prefix": prefix, "format": "mp4", "codec": "h264"}},
    }
