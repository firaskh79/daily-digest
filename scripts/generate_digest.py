#!/usr/bin/env python3
"""
Daily Cultural Digest Generator
Runs via GitHub Actions — no laptop required.
"""

import os
import json
import re
import glob
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import anthropic

DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")
REPO_ROOT = Path(__file__).parent.parent


# ─── Data fetchers ────────────────────────────────────────────────────────────

def fetch_apple_music_uk():
    try:
        r = requests.get(
            "https://kworb.net/charts/apple/gb.html",
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0 (compatible; DigestBot/1.0)"},
        )
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        tracks = []
        if table:
            for i, row in enumerate(table.find_all("tr")[1:13], 1):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    tracks.append({"pos": i, "raw": cells[1].get_text(strip=True)})
        return tracks
    except Exception as e:
        return [{"error": str(e)}]


def fetch_uk_news():
    try:
        r = requests.get(
            "https://news.google.com/rss?hl=en-GB&gl=GB&ceid=GB:en",
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        soup = BeautifulSoup(r.text, "xml")
        items = soup.find_all("item")[:20]
        return [
            {
                "title": item.find("title").text,
                "source": item.find("source").text if item.find("source") else "",
            }
            for item in items
        ]
    except Exception as e:
        return [{"error": str(e)}]


def fetch_world_news():
    try:
        r = requests.get(
            "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-GB&gl=GB&ceid=GB:en",
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        soup = BeautifulSoup(r.text, "xml")
        items = soup.find_all("item")[:20]
        return [
            {
                "title": item.find("title").text,
                "source": item.find("source").text if item.find("source") else "",
            }
            for item in items
        ]
    except Exception as e:
        return [{"error": str(e)}]


def fetch_annahar():
    try:
        r = requests.get(
            "https://www.annahar.com/arabic",
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        soup = BeautifulSoup(r.text, "html.parser")
        headlines = []
        for tag in soup.find_all(["h1", "h2", "h3"])[:25]:
            text = tag.get_text(strip=True)
            if len(text) > 10:
                headlines.append(text)
        return headlines[:12]
    except Exception as e:
        return [f"Error: {e}"]


def fetch_tiktok():
    try:
        r = requests.get(
            "https://tokchart.com/charts/global-sounds",
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        soup = BeautifulSoup(r.text, "html.parser")
        sounds = []
        for item in soup.find_all(class_=re.compile(r"chart|track|sound|entry|row"))[:15]:
            text = item.get_text(separator=" ", strip=True)
            if len(text) > 5:
                sounds.append(text[:120])
        return sounds[:8] if sounds else ["TikTok data unavailable"]
    except Exception as e:
        return [f"Error: {e}"]


# ─── Claude API calls ─────────────────────────────────────────────────────────

def generate_trends_json(client, raw):
    prompt = f"""You are a cultural intelligence analyst. Today is {DATE}.

Raw data fetched from live sources:

APPLE MUSIC UK TOP 12 (kworb.net):
{json.dumps(raw['apple_music'], indent=2)}

UK NEWS HEADLINES (Google News):
{json.dumps(raw['uk_news'], indent=2)}

WORLD NEWS HEADLINES (Google News):
{json.dumps(raw['world_news'], indent=2)}

ANNAHAR LEBANON HEADLINES (Arabic):
{json.dumps(raw['annahar'], indent=2)}

TIKTOK TRENDING SOUNDS:
{json.dumps(raw['tiktok'], indent=2)}

Synthesise all of this into a structured cultural intelligence JSON. Be specific — use real names, real headlines, real songs from the data above. Do not invent data. Where data is missing, say so honestly.

Return ONLY valid JSON (no markdown fences, no explanation) matching this schema exactly:

{{
  "date": "{DATE}",
  "mood_of_day": "conflicted",
  "macro": {{
    "politics": [
      {{"headline": "...", "tags": ["conflict"], "sentiment": "anxious", "intensity": 8}}
    ],
    "economics": [
      {{"headline": "...", "tags": ["markets"], "sentiment": "volatile", "intensity": 7}}
    ],
    "google_trends_uk": [
      {{"rank": 1, "term": "...", "volume_est": "500K+"}}
    ],
    "pytrends_uk_live": []
  }},
  "culture": {{
    "music": {{
      "apple_music_uk_top12": [
        {{"pos": 1, "artist": "...", "title": "...", "change": 0, "uk_artist": true, "mood_tags": ["intimate"], "theme_tags": ["love"]}}
      ],
      "tiktok_sounds": [
        {{"title": "...", "artist": "...", "score": 950, "videos": 0, "views": 0, "mood_tags": ["melancholic"], "theme_tags": ["longing"]}}
      ],
      "new_releases": []
    }},
    "film": {{
      "cannes_picks": [],
      "notable": []
    }},
    "tiktok_formats": []
  }},
  "cultural_acts": [
    {{
      "figure": "...",
      "type": "statement",
      "context": "...",
      "event_description": "...",
      "political_valence": "anti-authoritarian",
      "topics": ["..."],
      "explicit_targets": [],
      "backlash": null,
      "vs_discourse": "...",
      "reach": "viral"
    }}
  ],
  "streets": {{
    "protests": [
      {{"location": "...", "cause": "...", "scale": "...", "organiser": "...", "explicit_demand": "...", "counter_protest": null, "cross_border": false}}
    ],
    "summary": "..."
  }},
  "fashion": {{
    "current_fashion_week": null,
    "trend_signal": "..."
  }},
  "art_scene": {{
    "current_fairs": [],
    "notable_works_or_shows": [],
    "auction_signals": "..."
  }},
  "discourse": {{
    "realist_academics": [],
    "nationalist_media": [
      {{"figure": "...", "outlet": "...", "geo": "UK", "framing": "...", "topics": ["..."], "vs_realists": "independent"}}
    ],
    "convergence_points": [],
    "divergence_points": []
  }},
  "podcasts": [],
  "media_framing": [
    {{
      "outlet": "Annahar",
      "geo": "Lebanon",
      "political_lean": "Lebanese liberal",
      "lead_story": "...",
      "framing": "...",
      "diverges_from_anglophone": true,
      "divergence_note": "..."
    }}
  ],
  "silence_detector": [
    {{"macro_event": "...", "intensity": 7, "registers_silent": ["music", "fashion"], "observation": "..."}}
  ],
  "synthesis": {{
    "daily_theme": "...",
    "mechanism": "...",
    "leading_signals": ["..."],
    "connections": [
      {{
        "macro_event": "...",
        "cultural_response": "...",
        "mechanism": "...",
        "observation": "...",
        "confidence": "moderate",
        "signal_type": "reactive",
        "tags": ["..."]
      }}
    ]
  }}
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    # Strip markdown fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        text = match.group(1)
    return json.loads(text)


def generate_html_digest(client, data):
    prompt = f"""You are generating a daily cultural intelligence digest as a self-contained HTML page.
Today is {DATE}. Here is the full cultural intelligence data:

{json.dumps(data, indent=2)}

Generate a complete HTML page. Requirements:

DESIGN SYSTEM (use CSS variables):
--bg: #0a0a0f | --surface: #13131a | --border: #1f1f2e
--purple: #a78bfa | --blue: #60a5fa | --green: #34d399 | --amber: #fbbf24 | --red: #f87171
Font: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
Dark background, light text (#e8e6e3), subtle card borders, hover effects

SECTIONS (in this order):
1. Header — gradient title "Cultural Intelligence", date, mood badge with colour matching mood
2. Executive Summary — 3-4 bullet signals, one-paragraph synthesis
3. Political & Economic Pulse — cards with intensity bars (coloured by severity), tags
4. Google Trends UK — grid of rank cards
5. Music — Apple Music UK chart (pos number, change arrow, artist, title, UK badge if UK artist, mood tags), then TikTok sounds
6. Cultural Acts & Statements — cards with figure name, context, description, backlash note if any, reach badge
7. Streets & Protests — location, scale, cause, demand
8. Discourse & Media Framing — academics and media outlets, then Annahar section with Arabic RTL text, right-aligned, in a purple-bordered card
9. Synthesis — highlighted theme quote, connections with confidence badges (strong=green, moderate=amber, speculative=grey), leading signals

RULES:
- No external dependencies (no CDN, no Google Fonts — use system fonts)
- Fully self-contained single HTML file
- All data must come from the JSON above — do not invent anything
- Arabic text must be in a dir="rtl" container
- Intensity bars: 1-10 scale, color red if ≥8, amber if ≥6, green otherwise

Return ONLY the complete HTML starting with <!DOCTYPE html>. No explanation, no markdown."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()


# ─── Index regenerator ────────────────────────────────────────────────────────

def update_index():
    dates = sorted(
        [
            re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1)
            for f in glob.glob(str(REPO_ROOT / "daily-digest-*.html"))
            if re.search(r"(\d{4}-\d{2}-\d{2})", f)
        ],
        reverse=True,
    )

    rows = ""
    for i, d in enumerate(dates):
        has_json = (REPO_ROOT / "data" / f"trends-{d}.json").exists()
        latest = '<span class="latest-badge">Latest</span>' if i == 0 else ""
        card_class = "digest-card latest" if i == 0 else "digest-card"
        trends_btn = (
            f'<a class="btn btn-data" href="trends-viewer.html?date={d}">📊 Trends</a>'
            if has_json
            else ""
        )
        rows += f"""
    <div class="{card_class}">
      <div><span class="date-label">{d}</span>{latest}</div>
      <div class="links">
        <a class="btn btn-digest" href="daily-digest-{d}.html">📰 Digest</a>
        {trends_btn}
      </div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Cultural Digest</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0a0a0f; color: #e8e6e3; min-height: 100vh; padding: 48px 24px; }}
  .container {{ max-width: 720px; margin: 0 auto; }}
  header {{ margin-bottom: 48px; }}
  h1 {{ font-size: 2rem; font-weight: 700; letter-spacing: -0.02em;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }}
  .subtitle {{ color: #6b7280; font-size: 0.95rem; }}
  .digest-list {{ display: flex; flex-direction: column; gap: 16px; }}
  .digest-card {{ background: #13131a; border: 1px solid #1f1f2e; border-radius: 12px;
    padding: 24px; display: flex; align-items: center; justify-content: space-between;
    gap: 16px; transition: border-color 0.2s; }}
  .digest-card:hover {{ border-color: #a78bfa44; }}
  .digest-card.latest {{ border-color: #a78bfa66; }}
  .date-label {{ font-size: 1.1rem; font-weight: 600; }}
  .latest-badge {{ display: inline-block; background: #a78bfa22; color: #a78bfa;
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
    padding: 3px 10px; border-radius: 20px; margin-left: 10px; vertical-align: middle; }}
  .links {{ display: flex; gap: 10px; flex-shrink: 0; }}
  .btn {{ display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px;
    border-radius: 8px; font-size: 0.85rem; font-weight: 500; text-decoration: none; transition: background 0.2s; }}
  .btn-digest {{ background: #a78bfa22; color: #a78bfa; border: 1px solid #a78bfa44; }}
  .btn-digest:hover {{ background: #a78bfa33; }}
  .btn-data {{ background: #60a5fa22; color: #60a5fa; border: 1px solid #60a5fa44; }}
  .btn-data:hover {{ background: #60a5fa33; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>Daily Cultural Digest</h1>
    <p class="subtitle">Cultural intelligence — updated every morning</p>
  </header>
  <div class="digest-list">{rows}
  </div>
</div>
</body>
</html>"""

    (REPO_ROOT / "index.html").write_text(html, encoding="utf-8")
    print(f"index.html updated with {len(dates)} entries")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    print(f"=== Daily Cultural Digest: {DATE} ===")

    print("Fetching live data...")
    raw = {
        "apple_music": fetch_apple_music_uk(),
        "uk_news": fetch_uk_news(),
        "world_news": fetch_world_news(),
        "annahar": fetch_annahar(),
        "tiktok": fetch_tiktok(),
    }
    print(f"  Apple Music: {len(raw['apple_music'])} tracks")
    print(f"  UK news: {len(raw['uk_news'])} headlines")
    print(f"  World news: {len(raw['world_news'])} headlines")
    print(f"  Annahar: {len(raw['annahar'])} headlines")

    print("Generating trends JSON via Claude API...")
    trends = generate_trends_json(client, raw)

    data_dir = REPO_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    json_path = data_dir / f"trends-{DATE}.json"
    json_path.write_text(json.dumps(trends, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {json_path}")

    print("Generating HTML digest via Claude API...")
    html = generate_html_digest(client, trends)

    html_path = REPO_ROOT / f"daily-digest-{DATE}.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"Saved {html_path}")

    print("Updating index.html...")
    update_index()

    print("=== Done ===")


if __name__ == "__main__":
    main()
