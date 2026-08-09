from enum import Enum


class Intent(Enum):
    SUMMARY = "summary"
    METHODS = "methods"
    LIMITATIONS = "limitations"
    APPLICATIONS = "applications"
    COMPARE = "compare"
    AUTHOR = "author"
    SECTION = "section"
    UNKNOWN = "unknown"


class RetrievalRoute:
    def __init__(self, intent, queries, section_filter=None, use_vector_search=True, use_reranker=True, needs_comparison=False):
        self.intent = intent
        self.queries = queries
        self.section_filter = section_filter
        self.use_vector_search = use_vector_search
        self.use_reranker = use_reranker
        self.needs_comparison = needs_comparison


METHOD_QUERY_TERMS = ["methods", "approaches", "framework", "architecture", "modules"]
INTENT_QUERY_TERMS = {
    Intent.SUMMARY: ["summary", "main ideas", "contributions", "findings", "overview"],
    Intent.METHODS: METHOD_QUERY_TERMS,
    Intent.LIMITATIONS: ["limitations", "challenges", "failures", "weaknesses", "future work"],
    Intent.APPLICATIONS: ["applications", "use cases", "tasks", "domains", "practical uses"],
    Intent.COMPARE: ["comparison", "differences", "advantages", "tradeoffs", "versus"],
    Intent.AUTHOR: ["authors", "title", "front matter", "paper header", "affiliations"],
    Intent.SECTION: ["section", "heading", "part", "topic", "outline"],
    Intent.UNKNOWN: ["summary", "main ideas", "methods", "findings", "limitations"],
}
SECTION_FILTER_TERMS = {
    "experiments": ["experiment", "experiments", "evaluation", "results"],
    "future": ["future", "discussion", "conclusion", "limitations"],
    "conclusion": ["conclusion", "discussion", "future"],
}


def classify_intent(query):
    normalized_query = query.lower()

    # Check limitations/future-work before author: "what future work do the
    # authors suggest" mentions authors but is not an author question.
    if any(term in normalized_query for term in ["limitation", "limitations", "challenge", "challenges", "fail", "failure", "weakness", "future", "future work", "future direction", "future directions"]):
        return Intent.LIMITATIONS
    if any(term in normalized_query for term in ["author", "authors", "wrote", "written by", "title"]):
        return Intent.AUTHOR
    if any(term in normalized_query for term in ["compare", "comparison", "versus", "vs", "difference", "different"]):
        return Intent.COMPARE
    if any(term in normalized_query for term in ["application", "applications", "use case", "use cases", "used for", "where is"]):
        return Intent.APPLICATIONS
    if any(term in normalized_query for term in ["method", "methods", "approach", "approaches", "framework", "architecture", "module", "modules"]):
        return Intent.METHODS
    if any(term in normalized_query for term in ["section", "chapter", "part", "where does", "which section"]):
        return Intent.SECTION
    if any(term in normalized_query for term in ["summarize", "summary", "overview", "main", "overall", "contribution", "contributions"]):
        return Intent.SUMMARY

    return Intent.UNKNOWN


def detect_section_filter(query):
    normalized_query = query.lower()
    for terms in SECTION_FILTER_TERMS.values():
        if any(term in normalized_query for term in terms):
            return terms
    return None


def build_queries(intent, question):
    query_terms = INTENT_QUERY_TERMS[intent]
    # Always search with the user's actual wording, not just generic intent terms.
    return [question] + query_terms[:4]


def deterministic_route_query(question):
    intent = classify_intent(question)

    if intent == Intent.AUTHOR:
        return RetrievalRoute(
            intent=intent,
            queries=[],
            section_filter=["Front Matter"],
            use_vector_search=False,
            use_reranker=False,
        )

    return RetrievalRoute(
        intent=intent,
        queries=build_queries(intent, question),
        section_filter=detect_section_filter(question),
        use_vector_search=True,
        use_reranker=True,
    )
