# 🏗️ Architecture Diagrams

**Last Updated:** 2026-09-04
**Audience:** Engineers onboarding to the PhimNgan repository app, technical writers, ops.

These Mermaid diagrams document the runtime topology of the platform. They are
rendered automatically by GitHub, GitLab, VS Code (with Mermaid extension), and
most modern Markdown viewers.

> **Tip:** Mermaid `flowchart` and `stateDiagram-v2` blocks render natively on
> GitHub. To preview locally, install the "Markdown Preview Mermaid Support"
> VS Code extension or paste into <https://mermaid.live>.

---

## 1. System Topology — services and their dependencies

High-level view: how the three apps (web, API, worker) connect to each other
and to external infrastructure.

```mermaid
flowchart TB
    subgraph Client["Browser"]
        UI[Next.js 14 App<br/>apps/web]
    end

    subgraph Server["App Servers"]
        API[FastAPI<br/>apps/api/python<br/>:8000]
        Worker[Temporal Worker<br/>apps/worker/python]
    end

    subgraph Infra["Infrastructure (docker-compose / K8s)"]
        DB[(PostgreSQL<br/>:5432)]
        Redis[(Redis<br/>:6379)]
        Temporal[Temporal Server<br/>:7233]
        S3[(S3 / R2 / GCS<br/>object storage)]
    end

    subgraph External["External Providers"]
        OpenAI[OpenAI / Anthropic / Gemini<br/>Translation LLMs]
        WhisperX[WhisperX<br/>ASR]
        TTS[TTS providers<br/>Azure, Google, ElevenLabs, ...]
        HF[HuggingFace<br/>pyannote, wav2vec2]
    end

    UI -->|REST + SSE| API
    UI -.->|Proxied uploads| S3
    API -->|SQLAlchemy| DB
    API -->|Cache, locks| Redis
    API -->|Start workflow| Temporal
    Temporal -->|Activity task| Worker
    Worker -->|Read/write data| DB
    Worker -->|Download models| HF
    Worker -->|TTS API calls| TTS
    Worker -->|LLM API calls| OpenAI
    Worker -->|Run ASR| WhisperX
    Worker -->|Read assets / Write renders| S3

    classDef client fill:#0c4a6e,color:#fff;
    classDef server fill:#7c2d12,color:#fff;
    classDef infra fill:#14532d,color:#fff;
    classDef ext fill:#4c1d95,color:#fff;
    class UI client;
    class API,Worker server;
    class DB,Redis,Temporal,S3 infra;
    class OpenAI,WhisperX,TTS,HF ext;
```

---

## 2. Workflow State Machine — Temporal pipeline lifecycle

The full dubbing pipeline is one Temporal workflow with eight named activities.
Each activity maps to one user-visible stage in the workspace Progress panel.

```mermaid
stateDiagram-v2
    [*] --> ingest: New project<br/>or upload

    ingest --> normalize_chinese: WhisperX<br/>returns raw ASR
    normalize_chinese --> translate_segments: Normalised<br/>segments persisted

    translate_segments --> translation_qa: LLM<br/>completed
    translation_qa --> subtitle_segment: QA passed<br/>(auto)
    translation_qa --> translate_segments: QA failed<br/>retry with feedback

    subtitle_segment --> tts_synthesize: Subtitles<br/>persisted
    tts_synthesize --> dubbing_align: TTS audio<br/>ready
    dubbing_align --> audio_mix: Aligned<br/>dubbing
    audio_mix --> render_build: Mixed track<br/>persisted
    render_build --> [*]: Video rendered

    state dubbing_align {
        [*] --> wav2vec2_align
        wav2vec2_align --> forced_align: wav2vec2 unavailable<br/>fallback
        forced_align --> [*]
    }

    note right of translation_qa
        QA flags include:
        - Untranslated segment
        - Length drift > 30%
        - Source/target language mismatch
    end note

    note right of render_build
        FFmpeg assembles:
        - Original video track
        - Dubbed VI audio
        - Optional background music
    end note
```

---

## 3. Provider Registry — pluggable LLM / TTS / ASR

The provider registry pattern (`apps/api/python/translator_api/providers/`)
lets us add new translation or TTS backends without changing call sites.

```mermaid
flowchart LR
    subgraph Caller["Worker activities"]
        Activity[activities_providers.py<br/>activities_phase3.py]
    end

    subgraph Registry["Provider Registry<br/>(registry.py)"]
        Bootstrap[bootstrap&#40;&#41;<br/>loads defaults]
        Dict[(provider_id → instance)]
    end

    subgraph Trans["Translation providers"]
        OpenAI[OpenAITranslator]
        Anthropic[AnthropicTranslator]
        Gemini[GeminiTranslator]
        Local[LocalLLMTranslator]
        Passthrough[PassthroughTranslator]
    end

    subgraph TTS["TTS providers"]
        Azure[AzureTTS]
        Google[GoogleTTS]
        ElevenLabs[ElevenLabsTTS]
        Edge[EdgeTTS]
        Qwen3[Qwen3TTS]
    end

    subgraph OCR["OCR providers"]
        CRAFT[CRAFTOCR]
        Easy[EasyOCR]
        Paddle[PaddleOCR]
    end

    Activity -->|provider_id| Registry
    Bootstrap --> Dict
    Dict --> Trans
    Dict --> TTS
    Dict --> OCR

    classDef caller fill:#0c4a6e,color:#fff;
    classDef reg fill:#7c2d12,color:#fff;
    classDef prov fill:#14532d,color:#fff;
    class Activity caller;
    class Bootstrap,Dict reg;
    class OpenAI,Anthropic,Gemini,Local,Passthrough,Azure,Google,ElevenLabs,Edge,Qwen3,CRAFT,Easy,Paddle prov;
```

**Adding a new provider** — see [`provider-guide.md`](./provider-guide.md).

---

## 4. Editor Data Flow — from REST to Zustand to React

How a single API list call makes its way into a panel component.

```mermaid
flowchart LR
    subgraph API["FastAPI"]
        Router[routers_editor.py]
        Repo[EditorRepository]
        Model[(transcript_segments<br/>table)]
    end

    subgraph Web["Next.js app"]
        Client[lib/api.ts<br/>api.listTranscript&#40;&#41;]
        Store[lib/store.ts<br/>Zustand]
        Panel[TranscriptPanel.tsx]
    end

    Router -->|SQLAlchemy| Repo
    Repo -->|SELECT| Model
    Router -->|JSON {segments, total}| Client
    Client -->|loadTranscript&#40;rows&#41;| Store
    Store -->|useEditor selector| Panel
    Panel -->|Skeleton / List / Empty| UI[Rendered UI]

    classDef api fill:#7c2d12,color:#fff;
    classDef web fill:#0c4a6e,color:#fff;
    class Router,Repo,Model api;
    class Client,Store,Panel,UI web;
```

---

## 5. SSE Streaming — real-time progress

The `useWorkflowStream` hook opens an EventSource to `/api/workflows/:id/events`
and pushes workflow state updates to the UI without polling.

```mermaid
sequenceDiagram
    participant Worker as Temporal Worker
    participant Temporal as Temporal Server
    participant API as FastAPI Route
    participant Hook as useWorkflowStream
    participant Panel as ProgressPanel

    Worker->>Temporal: complete_activity(stage_name)
    Temporal->>API: workflow_status_update (push)
    API->>Hook: SSE event { stage, status, progress_pct }
    Hook->>Panel: setSteps(nextSteps)
    Panel->>Panel: re-render stage dots
    Note over API,Panel: Reconnects every 5s<br/>on disconnect
```

---

## 6. Audio Mixing Pipeline

`useAudioMixer` + `apps/api/python/translator_api/routers_editor.py` mix
original audio, dubbed VI voice, and optional background music.

```mermaid
flowchart TB
    subgraph Input["Input tracks"]
        Orig[Original ZH audio<br/>.wav]
        Dub[Dubbed VI audio<br/>per-segment .wav]
        Music[Background music<br/>MP3 / WAV optional]
        SFX[SFX layer<br/>optional]
    end

    subgraph Mixer["Audio mixer (worker)"]
        Align[Activity: dubbing_align<br/>wav2vec2 forced alignment]
        Gain[Per-track gain<br/>original / vi / music / sfx]
        Mix[Activity: audio_mix<br/>FFmpeg amix filter]
    end

    subgraph Output
        Mixed[Mixed .wav<br/>ready for render]
    end

    Orig --> Align
    Dub --> Align
    Align --> Gain
    Music --> Gain
    SFX --> Gain
    Gain --> Mix
    Mix --> Mixed

    classDef in fill:#0c4a6e,color:#fff;
    classDef mix fill:#7c2d12,color:#fff;
    classDef out fill:#14532d,color:#fff;
    class Orig,Dub,Music,SFX in;
    class Align,Gain,Mix mix;
    class Mixed out;
```

---

## 📐 Rendering locally

```bash
# Option A — VS Code
code --install-extension bierner.markdown-mermaid

# Option B — mermaid-cli (PNG export)
npm install -g @mermaid-js/mermaid-cli
mmdc -i docs/architecture-diagrams.md -o out/architecture.png
```

---

## Related docs

- [`architecture.md`](./architecture.md) — narrative architecture description
- [`workflow.md`](./workflow.md) — pipeline details (non-visual)
- [`providers.md`](./providers.md) — provider registry details
- [`provider-guide.md`](./provider-guide.md) — how to add a new provider

---

**Maintained by:** AI Agent + Engineering
**Last reviewed:** 2026-09-04
