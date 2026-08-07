# CS6180 RAG MVP

Command-line MVP for indexing a research PDF, retrieving relevant chunks, and answering questions with grounded evidence.

## Setup

From the root folder, using **uv**:

```bash
uv sync
```

This creates `.venv` and installs everything pinned in `uv.lock`.

Or using plain **venv + pip**:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

For OpenAI answer generation, create a `.env` file in root folder:

```text
OPENAI_API_KEY=your_api_key_here
```

## Run the MVP

Run from the root folder.

With uv:

```bash
uv run python rag/app.py --pdf data/raw/your-paper.pdf
```

Or with a manually activated venv:

```powershell
.\.venv\Scripts\python.exe .\rag\app.py --pdf .\data\raw\your-paper.pdf
```

Ask a specific question:

```bash
uv run python rag/app.py --pdf data/raw/your-paper.pdf --query "What methods does this paper use?"
```

Use OpenAI for the final grounded answer:

```bash
uv run python rag/app.py --pdf data/raw/your-paper.pdf --query "What are the main contributions?" --answer-mode openai
```

Optionally change the retrieval size:

```bash
uv run python rag/app.py --pdf data/raw/your-paper.pdf --query "What are the limitations?" --top-k 5
```

Run optional benchmark evaluation with a gold file:

```bash
uv run python rag/app.py --pdf data/raw/your-paper.pdf --evaluate --gold-file outputs/bert_gold.md
```

## Notes

- `--pdf` is required.
- `--top-k` is optional; the retriever may internally broaden multi-query retrieval before reranking.
- Default answer mode is `extractive`, which does not require an OpenAI API key.
- Use `--answer-mode openai` only after setting `OPENAI_API_KEY`.
