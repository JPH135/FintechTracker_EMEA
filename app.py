"""
Flask server for the EMEA Fintech News Aggregator.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, jsonify, send_from_directory

from fetcher import fetch_articles
from summariser import summarise_article

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", static_url_path="")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.post("/api/refresh")
def refresh():
    """
    Fetch latest fintech articles, summarise each with Claude in parallel,
    and return the structured results as JSON.
    """
    try:
        articles = fetch_articles()
    except Exception as exc:
        logger.error("Feed fetch failed: %s", exc)
        return jsonify({"error": "Failed to fetch news feeds. Please try again."}), 502

    if not articles:
        return jsonify({"results": [], "message": "No articles found."})

    results = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(summarise_article, a): a for a in articles}
        for future in as_completed(futures):
            try:
                summary = future.result()
                if summary:
                    results.append(summary)
            except Exception as exc:
                logger.warning("Summarise task failed: %s", exc)

    # Sort by published date descending
    results.sort(key=lambda r: r.get("published", ""), reverse=True)

    return jsonify({"results": results})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
