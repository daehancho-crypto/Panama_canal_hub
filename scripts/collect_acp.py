#!/usr/bin/env python3
"""ACP public-page link snapshot. No AI or paid API calls."""
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

SOURCES = {
    "advisory": "https://pancanal.com/en/maritime-services/advisory-to-shipping/",
    "notices": "https://pancanal.com/en/maritime-services/notices-to-shipping/",
}
OUT = Path("data/acp_documents.json")
USER_AGENT = "PanamaCanalHub/1.0 (public notices monitoring; GitHub Actions)"
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.href = None
        self.words = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.words = []
    def handle_data(self, data):
        if self.href is not None:
            self.words.append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append((self.href, " ".join(" ".join(self.words).split())))
            self.href = None
            self.words = []

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=35) as resp:
        return resp.read(), resp.geturl(), resp.headers.get("Content-Type", "")

def main():
    old = json.loads(OUT.read_text()) if OUT.exists() else {}
    documents = {d["url"]: d for d in old.get("documents", [])}
    errors = []
    successes = 0
    now = datetime.now(timezone.utc).isoformat()
    for category, source in SOURCES.items():
        try:
            body, final_url, content_type = fetch(source)
            if "html" not in content_type.lower() and not body.lstrip().startswith(b"<"):
                raise ValueError("Unexpected non-HTML response")
            parser = Links()
            parser.feed(body.decode("utf-8", errors="replace"))
            found = 0
            for href, title in parser.links:
                url = urljoin(final_url, href).split("#")[0]
                host = urlparse(url).hostname or ""
                if not (host == "pancanal.com" or host.endswith(".pancanal.com")):
                    continue
                # Only collect linked PDFs; do not claim the listing is exhaustive.
                if not re.search(r"\.pdf(?:\?|$)", url, re.I):
                    continue
                found += 1
                if url not in documents:
                    documents[url] = {"url": url, "title": title or "ACP PDF", "category": category, "first_seen": now}
                elif title and documents[url].get("title") == "ACP PDF":
                    documents[url]["title"] = title
            if not found:
                raise ValueError("No PDF links found; page structure may have changed")
            successes += 1
        except Exception as exc:
            errors.append({"source": category, "error": str(exc)[:250]})
    if successes == 0:
        raise SystemExit("No ACP pages parsed successfully; keeping last good data: " + str(errors))
    result = {
        "sources": SOURCES,
        "last_successful_check": now,
        "warnings": errors,
        "documents": sorted(documents.values(), key=lambda d: (d.get("first_seen", ""), d["url"]), reverse=True),
        "disclaimer": "Links only. PDF content, replacement versions, effective dates and legal applicability are NOT verified."
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("PDF links stored:", len(documents), "source errors:", len(errors))
if __name__ == "__main__":
    main()
