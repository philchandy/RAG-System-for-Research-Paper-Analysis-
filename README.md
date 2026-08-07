# CS6180 RAG MVP

Command-line MVP for indexing research PDFs, retrieving relevant chunks, and answering questions with grounded evidence.

## Features

- **PDF ingestion built for research papers** — PyMuPDF extraction with column-aware reading order for two-column layouts, ligature expansion, and automatic removal of references/appendices.
- **Section-aware chunking** — heuristic section-header detection labels every chunk (Abstract, Introduction, Experiments, ...) so retrieval and answers can cite where evidence came from.
- **Multi-document querying** — index several PDFs and ask questions across all of them at once; each paper keeps its own document id.
- **LLM query planning with deterministic fallback** — an OpenAI planner turns each question into an intent plus 3–5 targeted search queries; without an API key it falls back to a keyword-based router.
- **Hybrid retrieval** — every planned query runs against both the Chroma vector store (semantic) and a BM25 index (lexical), with all result sets fused via Reciprocal Rank Fusion.
- **Cross-encoder reranking** — a `bge-reranker-base` model re-scores fused candidates against the original question.
- **Metadata fast paths** — author/title questions skip vector search and read Front Matter chunks directly.
- **Grounded answers with citations** — answers are generated only from retrieved evidence and must cite chunk IDs; extractive mode works fully offline, OpenAI mode produces fluent grounded summaries.
- **Five-part paper summaries with follow-ups** — a fixed query set covers problem, method, datasets, results, and limitations, plus follow-up question generation.
- **Benchmark evaluation** — optional scoring of generated summaries against manually written gold references (coverage, hallucination, keyword matching).

## Setup

From the root folder, using **uv**:

```bash
uv sync
```

This creates `.venv` and installs everything pinned in `uv.lock`.

Or using plain **venv + pip**:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

(On Windows: `.\.venv\Scripts\activate` instead of the `source` line.)

For OpenAI answer generation, create a `.env` file in the root folder:

```text
OPENAI_API_KEY=your_api_key_here
```

## Run the app

Run from the root folder. Every command below works two ways:

- **uv**: prefix with `uv run` (no activation needed)
- **plain python**: activate the venv first (`source .venv/bin/activate`), then use `python`

Index and query a PDF:

```bash
uv run python -m rag.app --pdf data/raw/your-paper.pdf
# or
python -m rag.app --pdf data/raw/your-paper.pdf
```

Query multiple PDFs at once (evidence is retrieved across all of them):

```bash
uv run python -m rag.app --pdf data/raw/paper-one.pdf data/raw/paper-two.pdf --query "How do these papers differ?"
# or
python -m rag.app --pdf data/raw/paper-one.pdf data/raw/paper-two.pdf --query "How do these papers differ?"
```

Ask a specific question:

```bash
uv run python -m rag.app --pdf data/raw/your-paper.pdf --query "What methods does this paper use?"
# or
python -m rag.app --pdf data/raw/your-paper.pdf --query "What methods does this paper use?"
```

Use OpenAI for the final grounded answer:

```bash
uv run python -m rag.app --pdf data/raw/your-paper.pdf --query "What are the main contributions?" --answer-mode openai
# or
python -m rag.app --pdf data/raw/your-paper.pdf --query "What are the main contributions?" --answer-mode openai
```

Optionally change the retrieval size:

```bash
uv run python -m rag.app --pdf data/raw/your-paper.pdf --query "What are the limitations?" --top-k 5
# or
python -m rag.app --pdf data/raw/your-paper.pdf --query "What are the limitations?" --top-k 5
```

Run optional benchmark evaluation with a gold file:

```bash
uv run python -m rag.app --pdf data/raw/your-paper.pdf --evaluate --gold-file outputs/bert_gold.md
# or
python -m rag.app --pdf data/raw/your-paper.pdf --evaluate --gold-file outputs/bert_gold.md
```

## Notes

- `--pdf` is required and accepts one or more paths; each PDF is indexed under its own document id.
- `--top-k` is optional; the retriever may internally broaden multi-query retrieval before reranking.
- Default answer mode is `extractive`, which does not require an OpenAI API key.
- Use `--answer-mode openai` only after setting `OPENAI_API_KEY`.
