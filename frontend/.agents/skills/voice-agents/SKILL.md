---
name: voice-agents
description: Speech-to-text, audio visualization, and turn-taking interaction.
---

# Voice Agents & Audio Telemetry

Specializes in voice interactions, conversational turn-taking, and live audio processing:

## 1. Conversational Voice Pipelines
- **Speech-to-Text (STT)**: Low-latency streaming transcription and voice activity detection (VAD).
- **Text-to-Speech (TTS)**: Streaming synthesized audio chunks with seamless playback queuing.
- **Barge-In Handling**: Interrupt TTS synthesis immediately upon user speech detection.

## 2. Turn-Taking Discipline
- Distinguish between active listening, user pauses, and completion of user turns.
- Provide immediate visual confirmation (VoiceStrip telemetry) when wake words or speech are detected.
