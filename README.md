# CS6180 RAG MVP

Command-line MVP for indexing a research PDF, retrieving relevant chunks, and answering questions with grounded evidence.

## Setup

From the root folder:

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

Run from the root folder:

```powershell
.\.venv\Scripts\python.exe .\mvp\mvp_demo.py --pdf .\data\raw\your-paper.pdf
```

Ask a specific question:

```powershell
.\.venv\Scripts\python.exe .\mvp\mvp_demo.py --pdf .\data\raw\your-paper.pdf --query "What methods does this paper use?"
```

Use OpenAI for the final grounded answer:

```powershell
.\.venv\Scripts\python.exe .\mvp\mvp_demo.py --pdf .\data\raw\your-paper.pdf --query "What are the main contributions?" --answer-mode openai
```

Optionally change the retrieval size:

```powershell
.\.venv\Scripts\python.exe .\mvp\mvp_demo.py --pdf .\data\raw\your-paper.pdf --query "What are the limitations?" --top-k 5
```

Run optional benchmark evaluation with a gold file:

```powershell
.\.venv\Scripts\python.exe .\mvp\mvp_demo.py --pdf .\data\raw\your-paper.pdf --evaluate --gold-file .\outputs\bert_gold.md
```

## Notes

- `--pdf` is required.
- `--top-k` is optional; the retriever may internally broaden multi-query retrieval before reranking.
- Default answer mode is `extractive`, which does not require an OpenAI API key.
- Use `--answer-mode openai` only after setting `OPENAI_API_KEY`.
