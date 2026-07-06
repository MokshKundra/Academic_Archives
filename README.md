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
- Python 3.12 recommended (3.11+ generally works, but avoid 3.15 — a few packages in `requirements.txt` don't support it yet)
- [Ollama](https://ollama.com) installed and running
- Poppler (required by `pdf2image` to convert PDF pages to images)

### Installing Poppler

**Windows:**

1. Download the latest release from [oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases) (grab the `Release-XX.XX.X-X.zip`)
2. Extract it somewhere permanent, e.g. `C:\poppler-26.02.0`
3. Note the full path to the `Library\bin` folder inside it, e.g. `C:\poppler-26.02.0\Library\bin` — you'll need this path for the `poppler_path` argument in `pdf_upload.py`
4. Update the `poppler_path` in `pdf_upload.py` to match your install location:

```python
images = convert_from_path(
    pdf_path,
    dpi=200,
    poppler_path=r"C:\poppler-26.02.0\Library\bin"  # ← update this
)
```

Alternatively, add the `Library\bin` folder to your Windows PATH environment variable, and you can drop the `poppler_path` argument entirely.

**macOS:**

```bash
brew install poppler
```

No `poppler_path` needed — it installs to a location already on your PATH.

**Linux (Debian/Ubuntu):**

```bash
sudo apt install poppler-utils
```

No `poppler_path` needed.

**Verify it's working:**

```bash
pdftoppm -v
# should print a version number, not "command not found"
```

### Install

```bash
git clone https://github.com/MokshKundra/Academic_Archives
cd Academic_Archives

python -m venv venv

# Activate the virtual environment
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

> **Imports not resolving in your editor?** After activating the venv and installing requirements, your IDE may still be pointing at the system Python. In VS Code: `Cmd+Shift+P` → "Python: Select Interpreter" → pick the one at `./venv/bin/python`. Reload the window/terminal if the red squiggles don't clear right away.

### Configure

```bash
cp .env.example .env
```

Edit `.env` and set:
- Which provider each pipeline (extraction, embedding, generation) should use — `ollama`, `openai`, `gemini`, `groq`, or `huggingface` — see `config.py` for the exact setting names.
- An API key for any external provider you select, e.g. `OPENAI_API_KEY=sk-...`, `GEMINI_API_KEY=...`, `GROQ_API_KEY=...`, `HUGGINGFACE_API_KEY=...`.

If you keep everything on the Ollama presets (`doc-extractor`, `nomic-embed-text`, `qwen3:8b`), no API keys are needed at all — only add keys for the providers you actually switch on.

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