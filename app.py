"""
Flask server for the EMEA Fintech News Aggregator.
"""

import logging

from flask import Flask, jsonify, send_from_directory

from fetcher import fetch_articles

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", static_url_path="")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.post("/api/refresh")
def refresh():
    """
    Fetch latest fintech articles from RSS feeds and return structured results as JSON.
    """
    try:
        articles = fetch_articles()
    except Exception as exc:
        logger.error("Feed fetch failed: %s", exc)
        return jsonify({"error": "Failed to fetch news feeds. Please try again."}), 502

    if not articles:
        return jsonify({"results": [], "message": "No articles found."})

    results = [
        {
            "company_name": a["title"],
            "story_summary": a.get("summary") or a.get("article_text", "")[:500],
            "location": None,
            "sub_vertical": "other",
            "investors": [],
            "key_metrics": None,
            "url": a["url"],
            "source": a["source"],
            "published": a["published"].isoformat(),
        }
        for a in articles
    ]

    return jsonify({"results": results})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
