import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("RAG_DATA_DIR", BASE_DIR / "data" / "raw"))
CHROMA_DIR = Path(os.getenv("RAG_CHROMA_DIR", BASE_DIR / "data" / "chroma"))
OUTPUTS_DIR = BASE_DIR / "outputs"
DEFAULT_GOLD_PATH = OUTPUTS_DIR / "bert_gold.md"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "BAAI/bge-reranker-base"
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 150

SUMMARY_QUERIES = {
	"problem": "What is the motivating problem that this paper aims to solve?",
	"method": "What method, model, or training approach does this paper use?",
	"dataset": "What datasets or data sources does this paper use?",
	"results": "What datasets, benchmarks, and results are reported in this paper?",
	"limitations": "What limitations, costs, or failure cases does this paper report?",
}

SUMMARY_SECTION_HINTS = {
	"problem": ["introduction", "abstract", "background"],
	"method": ["method", "methods", "star methods", "materials and methods", "approach"],
	"dataset": ["dataset", "data", "materials and methods", "experiments"],
	"results": ["results", "experiments", "evaluation", "discussion"],
	"limitations": ["limitations", "discussion", "conclusion", "future work", "outlook"],
}


DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
