Justin Gubbens, David Kim, Phillip Chandy  
CS6180 \- Foundations for Generative AI  
Final Project Proposal

**Project Topic and Problem Statement:**

Academic research papers are time-consuming to read through and not easy to understand to people outside of their field. While generic summaries such as abstracts capture the overall picture of the work being done, they are not sufficient to fully understand the methods used in the research in depth. Rather, to gain this understanding, it is usually necessary to read through the entire document, taking much time and effort.

For our project, we plan to build a research paper analysis agent capable of reviewing academic papers and responding to questions about their content. Rather than just giving a summary of the work, the agent will be able to decompose the paper into core components, including problem, method, dataset, results, and limitations, using an agentic pipeline. This tool will be useful for graduate students attempting to quickly assess whether a paper is relevant, understand its contributions, and prepare for deeper reading or discussion.

**Dataset/Inputs:** 

- Published research papers in a variety of fields, converted to text from PDF or provided as plain text
- Manually created reference answers for each paper, covering the main summary fields and a set of follow-up questions
- A small benchmark set of papers from different domains so we can test generalization across writing styles and research areas

**Evaluation Plan:**

- We will evaluate the responses of our agent over several categories  
  - Coverage score \- completeness of the initial summary compared to manually written references
  - Hallucination rate \- accuracy of the facts presented in the responses and how well they are grounded in the paper
  - Follow-up question accuracy \- performance on follow-up questions compared against manually written references
  - We will combine automatic scoring with manual review to check whether the agent gives useful, concise, and faithful answers

**Initial System Design and Planning:**

- The system will first extract the paper text, then break it into sections such as abstract, introduction, method, experiments, and conclusion.
- A retrieval and reasoning pipeline will identify the most relevant chunks for each question so the model can answer with citations to the source text.
- The agent will generate a structured summary with fields such as problem, proposed method, dataset, results, and limitations.
- For follow-up questions, the system will maintain context from previous turns and use the original paper as grounding evidence.
- We will evaluate the project with a small set of papers first, then refine prompts, chunking, and retrieval settings based on error analysis.

**Workload split:**

- Justin Gubbens \- paper collection, evaluation rubric design, and reference answer creation
- David Kim \- document parsing, chunking, and retrieval pipeline implementation
- Phillip Chandy \- agent prompting, response formatting, and follow-up question handling
- All team members \- testing, error analysis, and final writeup/presentation
Justin Gubbens, David Kim, Phillip Chandy  
CS6180 \- Foundations for Generative AI  
Final Project Proposal

**Project Topic and Problem Statement:**

Academic research papers are time-consuming to read through and not easy to understand to people outside of their field. While generic summaries such as abstracts capture the overall picture of the work being done, they are not sufficient to fully understand the methods used in the research in depth. Rather, to gain this understanding, it is usually necessary to read through the entire document, taking much time and effort.

For our project, we plan to build a research paper analysis agent capable of reviewing academic papers and responding to questions about their content. Rather than just giving a summary of the work, the agent will be able to decompose the paper into core components, including problem, method, dataset, results, and limitations, using an agentic pipeline. This tool will be useful for graduate students attempting to quickly assess whether a paper is relevant, understand its contributions, and prepare for deeper reading or discussion.

**Dataset/Inputs:** 

- Published research papers in a variety of fields, converted to text from PDF or provided as plain text
- Manually created reference answers for each paper, covering the main summary fields and a set of follow-up questions
- A small benchmark set of papers from different domains so we can test generalization across writing styles and research areas

**Evaluation Plan:**

- We will evaluate the responses of our agent over several categories  
  - Coverage score \- completeness of the initial summary compared to manually written references
  - Hallucination rate \- accuracy of the facts presented in the responses and how well they are grounded in the paper
  - Follow-up question accuracy \- performance on follow-up questions compared against manually written references
  - We will combine automatic scoring with manual review to check whether the agent gives useful, concise, and faithful answers

**Initial System Design and Planning:**

- The system will first extract the paper text, then break it into sections such as abstract, introduction, method, experiments, and conclusion.
- A retrieval and reasoning pipeline will identify the most relevant chunks for each question so the model can answer with citations to the source text.
- The agent will generate a structured summary with fields such as problem, proposed method, dataset, results, and limitations.
- For follow-up questions, the system will maintain context from previous turns and use the original paper as grounding evidence.
- We will evaluate the project with a small set of papers first, then refine prompts, chunking, and retrieval settings based on error analysis.

**Workload split:**

- Justin Gubbens \- paper collection, evaluation rubric design, and reference answer creation
- David Kim \- document parsing, chunking, and retrieval pipeline implementation
- Phillip Chandy \- agent prompting, response formatting, and follow-up question handling
- All team members \- testing, error analysis, and final writeup/presentation