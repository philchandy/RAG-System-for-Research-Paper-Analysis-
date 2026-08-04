from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"
CHROMA_DIR = BASE_DIR / "data" / "chroma"
OUTPUTS_DIR = BASE_DIR / "outputs"
GOLD_PATH = OUTPUTS_DIR / "bert_gold.md"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 150

SUMMARY_QUERIES = {
	"problem": "What problem or limitation of prior approaches does BERT solve?",
	"method": "What method or training approach does BERT use?",
	"results": "What datasets, benchmarks, and results are reported for BERT?",
}


DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
