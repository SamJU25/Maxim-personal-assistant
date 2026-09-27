# MaxIM Models Directory (Method B: Native Drag & Drop)

Welcome to the MaxIM local model repository!

### Organized Folder Layout
You can drop `.gguf` files directly into their respective capability folders, or drop them directly into `models/` (MaxIM will automatically understand their capability):

- **`models/llm/`** — **All-Rounder Reasoning Models** (General intelligence, coding, tool use, LifeOS task automation)
  - Examples: `Qwen3.5-9B-abliterated-Q4_K_M.gguf`, `Qwen3.5-4B-Q6_K.gguf`, `gemma-4-E4B-it-qat`
- **`models/vision/`** — **Multimodal Vision Models & Projectors** (Image analysis, screen inspection, OCR)
  - Examples: `Qwen3VL-4B-Instruct-Q4_K_M.gguf` + `mmproj-Qwen3VL-4B-Instruct-F16.gguf`
- **`models/embedding/`** — **Dense Vector & Neural Reranker Models** (Dense retrieval & reranking)
  - Examples: `Qwen3-Embedding-0.6B-Q8_0.gguf`, `Qwen3-Reranker-0.6B-q8_0.gguf`
- **`models/asr/`** — **Voice-to-Text Models** (Speech recognition, audio transcription)
  - Examples: `qwen3-asr-0.6b-q8_0.gguf`, `qwen3-asr-1.7b-q8_0.gguf`
- **`models/tts/`** — **Text-to-Voice Models** (Neural speech synthesis, voice cloning)
  - Examples: `qwen3-tts-12hz-0.6b-base-q8_0.gguf`, `voice_ref_16k.wav`
- **`models/reasoning/`** — **Dedicated Deep Thinking & Chain-of-Thought Models**

### How MaxIM Uses Them
MaxIM's intent classifier automatically evaluates incoming tasks:
- General chat & tool execution dispatches to **All-Rounder LLM**.
- Visual inspection or attached frames dispatch to **Vision Model** with paired `mmproj`.
- Vault search and long-term memory recall dispatch to **Embedding & Reranker**.
- Microphone input dispatches to **ASR Model** (audio.cpp on CUDA at ~12x realtime).
- Voice conversational replies dispatch to **TTS Model** (cloned to MaxIM's persona).

### Recommended Quantizations
- `Q4_K_M` (Optimal balance of speed, accuracy, and VRAM for 6GB RTX 4050)
- `Q8_0` / `Q6_K` (For smaller models like 0.6B embeddings/ASR or 4B LLMs)
