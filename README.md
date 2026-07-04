# Academic Archices

A local RAG (Retrieval-Augmented Generation) system for course materials.
Upload lecture slides, past year papers, notes, and textbooks — then chat with them.

## Stack
- **Backend**: FastAPI
- **Vector DB**: ChromaDB (persistent, local)
- **Extraction**: Available API end points: OpenAI, Gemini, Groq, HuggingFace; Ollama supported for local models(preset to: custom prompted minicpm-v "doc-extractor" explained at the end)
- **Embedding**: Available API end points: OpenAI, HuggingFace; Ollama supported for local models(preset to: nomic-embed-text)
- **Generation**: Available API end points: OpenAI, Gemini, Groq, HuggingFace; Ollama supported for local models(preset to: qwen3:8b)

## Setup

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com) installed and running
- [Poppler](https://github.com/oschwartz10612/poppler-windows/releases) (Windows)

### Install

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME
cd YOUR_REPO_NAME

python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# edit .env with your provider choices and API keys if using external providers
```

### Pull Ollama models

```bash
ollama pull minicpm-v
ollama pull nomic-embed-text
ollama pull qwen3:8b
```

### Run

```bash
uvicorn app:app --reload
```

API docs available at http://localhost:8000/docs

## Project structure

```
├── app.py              # FastAPI endpoints
├── pdf_upload.py       # PDF → text extraction pipeline
├── upload.py           # ChromaDB ingestion
├── retrival.py         # RAG retrieval + generation
├── chat_store.py       # Chat persistence (local files)
├── config.py           # Settings via pydantic-settings
├── providers/
│   ├── ext.py          # Extraction provider (ollama/openai/gemini)
│   └── gen.py          # Generation provider (ollama/openai/gemini/groq)
├── upload_schema.py    # Pydantic models for upload
└── query_schema.py     # Pydantic models for queries
```

## Setting up the `doc-extractor` model

The extraction pipeline uses a custom Ollama model built on top of `minicpm-v` with a
tuned system prompt for academic document transcription. You need to create it locally
before running the app.

### Prerequisites

Make sure you have `minicpm-v` pulled first:

```bash
ollama pull minicpm-v
```

### Create the model

1. Copy the `Modefile` from the root of this repo into your working directory (it's
   already there if you cloned the repo).

2. Run:

```bash
ollama create doc-extractor -f Modefile
```

3. Verify it was created:

```bash
ollama list
# should show doc-extractor in the list
```

### What the model does

`doc-extractor` is `minicpm-v` with a strict transcription-only system prompt. It:

- Outputs structured markdown with `### EXTRACTED_TEXT` and `### VISUAL_ELEMENTS` sections
- Transcribes handwritten text with a `**Handwritten:**` prefix
- Formats code blocks, tables, and math correctly
- Flags illegible content as `[ILLEGIBLE]` instead of guessing
- Suppresses noise like page numbers, university names, and camera artifacts

> **Note:** If you modify the `Modefile` and want to rebuild the model, run:
> ```bash
> ollama rm doc-extractor
> ollama create doc-extractor -f Modefile
> ```
