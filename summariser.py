"""
Uses Claude claude-sonnet-4-6 to extract structured information from each article.
Returns a structured dict or None if the article is not relevant.
"""

import json
import logging

import anthropic

from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a fintech analyst specialising in EMEA (Europe, Middle East, Africa) markets.
Your job is to read a news article and extract structured information about the fintech company or companies featured.

Return ONLY valid JSON. No markdown, no explanation, just the JSON object.

If the article is clearly not about a fintech company (e.g. a generic economic report, a non-fintech tech story, or completely unrelated content), return: {"relevant": false}

Otherwise return:
{
  "relevant": true,
  "company_name": "Primary company name featured in the article",
  "location": "City, Country (or region if city unknown)",
  "sub_vertical": "One of: payments | lending | wealthtech | regtech | insurtech | crypto | banking | embedded-finance | infrastructure | other",
  "investors": ["List of known investors or funding participants. Empty array if unknown."],
  "key_metrics": "Key business metrics mentioned: funding raised, ARR, number of customers/users, growth rate, valuation, transaction volume, etc. Write 'Not disclosed' if none mentioned.",
  "story_summary": "2-3 sentence summary of the news story itself."
}"""

USER_TEMPLATE = """Article title: {title}
Source: {source}

Article content:
{article_text}"""


def summarise_article(article: dict) -> dict | None:
    """
    Send an article to Claude and return the structured summary.
    Returns None if the article is not relevant or if the API call fails.
    """
    user_content = USER_TEMPLATE.format(
        title=article.get("title", ""),
        source=article.get("source", ""),
        article_text=article.get("article_text", article.get("summary", "")),
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = response.content[0].text.strip()
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("JSON parse error for article: %s", article.get("title"))
        return None
    except anthropic.APIError as exc:
        logger.error("Anthropic API error: %s", exc)
        return None

    if not data.get("relevant", False):
        return None

    # Attach metadata from the original article
    data["url"] = article.get("url", "")
    data["source"] = article.get("source", "")
    data["published"] = article.get("published", "").isoformat() if hasattr(
        article.get("published", ""), "isoformat"
    ) else str(article.get("published", ""))
    data["title"] = article.get("title", "")
    return data
