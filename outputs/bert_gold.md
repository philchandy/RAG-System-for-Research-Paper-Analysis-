# BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding

## problem
- Prior pre-training approaches were either feature-based or used unidirectional language models for fine-tuning, which limited contextual representation power.
- The paper identifies unidirectionality as a major limitation, especially for token-level tasks like question answering that need both left and right context.

## method
- BERT pre-trains deep bidirectional Transformer encoders using a masked language modeling (MLM) objective.
- BERT also uses next sentence prediction (NSP) to pre-train relationships between sentence pairs.
- Fine-tuning is task-specific but simple: initialize from one pre-trained model and add a small output layer while fine-tuning all parameters.
- Two core model configurations are reported: BERT_BASE (L=12, H=768, A=12, 110M params) and BERT_LARGE (L=24, H=1024, A=16, 340M params).

## dataset
- Pre-training data: BooksCorpus (about 800M words) and English Wikipedia (about 2,500M words).
- Evaluation includes major benchmarks across sentence-level and token-level tasks, including GLUE, MultiNLI, SQuAD v1.1, and SQuAD v2.0.

## results
- BERT reports state-of-the-art results on 11 NLP tasks in the paper.
- Reported headline numbers include GLUE 80.5, MultiNLI 86.7, SQuAD v1.1 F1 93.2, and SQuAD v2.0 F1 83.1.
- The paper emphasizes that these gains are achieved without substantial task-specific architecture modifications.

## limitations
- Pre-training is computationally expensive: large TPU resources are used, with pre-training runs reported as taking about 4 days.
- Longer sequence training is costly because self-attention scales quadratically with sequence length.
- Fine-tuning BERT_LARGE is reported as sometimes unstable on small datasets, requiring random restarts.
