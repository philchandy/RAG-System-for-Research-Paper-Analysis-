import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("RAG_DATA_DIR", BASE_DIR / "data" / "raw"))
CHROMA_DIR = Path(os.getenv("RAG_CHROMA_DIR", BASE_DIR / "data" / "chroma"))
OUTPUTS_DIR = BASE_DIR / "outputs"
DEFAULT_GOLD_PATH = OUTPUTS_DIR / "bert_gold.md"

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
RERANKER_MODEL = "BAAI/bge-reranker-base"
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 150

SUMMARY_TOP_K = 8

SUMMARY_QUERIES = {
	"problem": "What is the motivating problem that this paper aims to solve?",
	"method": "What method, model, or training approach does this paper use?",
	"dataset": "What datasets or data sources does this paper use?",
	"results": "What datasets, benchmarks, and results are reported in this paper?",
	"limitations": "What does this paper explicitly state as a limitation, unresolved question, or caveat of its own study, method, or results — not a limitation of prior work?",
}

SUMMARY_SECTION_HINTS = {
	"problem": ["introduction", "abstract", "background", "motivation", "summary", "front matter"],
	"method": ["method", "methods", "star methods", "materials and methods", "approach", "model", "system design", "architecture", "abstract", "summary"],
	"dataset": ["dataset", "data", "materials and methods", "experiments", "summary statistics", "sample", "abstract", "summary"],
	"results": ["results", "experiments", "evaluation", "discussion", "findings", "abstract", "summary", "front matter"],
	"limitations": ["limitations", "discussion", "conclusion", "future work", "outlook", "caveats"],
}


DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
