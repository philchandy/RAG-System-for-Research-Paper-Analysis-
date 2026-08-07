import json
import os

from dotenv import load_dotenv
import openai as OpenAI

from rag.answer import ENV_PATH
from rag.router import Intent, RetrievalRoute, deterministic_route_query


PLANNER_MODEL = "gpt-4o-mini"


def get_openai_client():
    load_dotenv(dotenv_path=ENV_PATH)
    if not os.getenv("OPENAI_API_KEY"):
        return None
    return OpenAI.OpenAI()


def build_planner_prompt(question):
    intents = ", ".join(intent.value for intent in Intent)
    return "\n".join(
        [
            "You are a retrieval planner for a research-paper RAG system.",
            "Given a user's question, generate a retrieval plan.",
            "Return JSON only. Do not include markdown.",
            "",
            "Allowed intents:",
            intents,
            "",
            "Return this JSON shape:",
            '{"intent":"...","queries":["..."],"metadata_filter":null,"needs_comparison":false}',
            "",
            "Rules:",
            "- Generate 0 queries only when metadata_filter alone is enough, such as author/title questions.",
            "- Otherwise generate 3 to 5 specific search queries based on the user's wording.",
            "- metadata_filter may be null or a section hint such as Front Matter, Experiments, Methods, Results, Discussion, Conclusion, Future Work, or Limitations.",
            "- Use intent author for title, authors, affiliation, or who-wrote questions.",
            "- Use intent compare when the question asks for differences, tradeoffs, versus, or comparison.",
            "",
            "Question:",
            question,
        ]
    )


def coerce_intent(value):
    try:
        return Intent(str(value).strip().lower())
    except ValueError:
        return Intent.UNKNOWN


def normalize_metadata_filter(metadata_filter):
    if metadata_filter is None:
        return None

    if isinstance(metadata_filter, list):
        values = [str(value).strip() for value in metadata_filter if str(value).strip()]
    else:
        values = [str(metadata_filter).strip()]

    if not values:
        return None

    normalized_values = []
    for value in values:
        lowered_value = value.lower()
        if lowered_value in ["none", "null", "any", "all"]:
            continue
        if lowered_value in ["front matter", "frontmatter", "header", "paper header"]:
            normalized_values.append("Front Matter")
        else:
            normalized_values.append(value)

    return normalized_values or None


def route_from_plan(plan, fallback_route):
    if not isinstance(plan, dict):
        return fallback_route

    intent = coerce_intent(plan.get("intent"))
    queries = plan.get("queries", [])
    if not isinstance(queries, list):
        queries = []
    queries = [str(query).strip() for query in queries if str(query).strip()][:5]
    section_filter = normalize_metadata_filter(plan.get("metadata_filter"))
    needs_comparison = bool(plan.get("needs_comparison", False))

    if intent == Intent.AUTHOR:
        return RetrievalRoute(
            intent=intent,
            queries=[],
            section_filter=["Front Matter"],
            use_vector_search=False,
            use_reranker=False,
            needs_comparison=needs_comparison,
        )

    if not queries:
        queries = fallback_route.queries

    return RetrievalRoute(
        intent=intent,
        queries=queries,
        section_filter=section_filter or fallback_route.section_filter,
        use_vector_search=True,
        use_reranker=True,
        needs_comparison=needs_comparison,
    )


def plan_query(question, model=PLANNER_MODEL):
    fallback_route = deterministic_route_query(question)
    client = get_openai_client()
    if client is None:
        return fallback_route

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Return retrieval plans as valid JSON only."},
                {"role": "user", "content": build_planner_prompt(question)},
            ],
            temperature=0,
        )
        plan_text = response.choices[0].message.content.strip()
        plan = json.loads(plan_text)
    except Exception:
        return fallback_route

    return route_from_plan(plan, fallback_route)
