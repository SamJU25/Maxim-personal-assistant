---
name: llm-and-rag-engineering
description: Production RAG, token budgeting, prompt caching, and MCP servers.
---

# LLM & RAG Engineering

Covers production RAG architectures, prompt optimization, token budgeting, and Model Context Protocol (MCP) server development:

## 1. Production RAG Pipelines
- **Chunking Strategies**: Semantic chunking, sliding windows, and code AST-aware splitting.
- **Embeddings & Vector Search**: Dense vector retrieval, hybrid BM25 search, and reciprocal rank fusion (RRF).
- **Retrieval Metrics**: Track context relevance, groundedness, and answer faithfulness.

## 2. LLM Cost Optimization & Prompt Engineering
- **Context Window Budgeting**: Respect the 80/20 Context Cliff; prevent prompt overflow.
- **Prompt Caching**: Structure static system instructions, schemas, and tools first to maximize cache hits.
- **Constrained Generation**: Enforce strict JSON schemas, regex grammars, and structured outputs.

## 3. Model Context Protocol (MCP) Development
- **Server Architecture**: Author standard MCP servers communicating over stdio or SSE.
- **Schema Design**: Define tight JSON Schema contracts for tool arguments with clear parameter descriptions.
- **Lazy Loading**: Register MCP servers in configuration; load tool schemas on demand.

## 4. Local Hardware Profiling & Model Quantization Sizing (Magnitude Architecture)
- **Host Capability Probing**: Automatically interrogate physical RAM, CPU logical cores, and GPU VRAM (via `nvidia-smi` or system drivers) prior to model deployment.
- **Quantization Footprint Matching**: Map available memory budgets to quantized weights to avoid operating system swap thrashing and out-of-memory (OOM) crashes:
  - `3B Q4_K_M`: ~2.2GB VRAM / ~3.0GB RAM (lightweight intent extraction, classification).
  - `7B/8B Q4_K_M`: ~5.5GB VRAM / ~7.0GB RAM (general code assistance, structured tool calls).
  - `14B Q4_K_M`: ~9.5GB VRAM / ~12.5GB RAM (deep reasoning, architectural audits).
  - `32B Q4_K_M`: ~20GB VRAM / ~24GB RAM (enterprise-scale reasoning).
  - `70B Q4_K_M`: ~42GB VRAM / ~48GB RAM (maximum open intelligence).
- **Execution Tier Assignment**: Classify execution feasibility into `optimal_gpu_full_speed`, `feasible_cpu_ram`, `tight_requires_app_closure`, or `exceeds_hardware_capacity`.
- **Throughput Calibration**: Benchmark local token generation speeds (tok/sec) to dynamically select between local inference and upstream cloud fallbacks.
