import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK = os.getenv("DISCORD_WEBHOOK")
JOOBLE_KEY = os.getenv("JOOBLE_API_KEY")

SEEN_FILE = "seen_jobs.json"
MAX_RESULTS = 12

WAREHOUSE_KEYWORDS = [
    "warehouse", "order picker", "logistics", "forklift",
    "magazijn", "lager", "skladnik", "production", "packing"
]

SEASONAL_KEYWORDS = [
    "summer", "seasonal", "july", "august", "temporary", "student", "part-time"
]

def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

# ---------------------------------------
# SINGLE JOOBLE REQUEST
# ---------------------------------------

def fetch_jooble():
    url = f"https://jooble.org/api/{JOOBLE_KEY}"

    # One powerful query that covers everything
    keywords = (
        "(" + " OR ".join(WAREHOUSE_KEYWORDS) + ") AND "
        "(" + " OR ".join(SEASONAL_KEYWORDS) + ")"
    )

    payload = {
        "keywords": keywords,
        "location": "Europe",
        "page": 1,
        "radius": 100
    }

    res = requests.post(url, json=payload)
    data = res.json()

    jobs = []
    for job in data.get("jobs", []):
        jobs.append({
            "id": job.get("link"),
            "title": job.get("title", ""),
            "desc": job.get("snippet", "").strip(),
            "link": job.get("link"),
            "source": "jooble"
        })

    return jobs

# ---------------------------------------
# SCORING
# ---------------------------------------

def score_job(job):
    text = (job["title"] + " " + job["desc"]).lower()

    score = 0

    if any(w in text for w in WAREHOUSE_KEYWORDS):
        score += 6

    if any(s in text for s in SEASONAL_KEYWORDS):
        score += 4

    if "student" in text or "part-time" in text:
        score += 2

    return min(score, 10)

# ---------------------------------------
# DISCORD
# ---------------------------------------

def send_to_discord(jobs):
    if not jobs:
        print("No jobs to send.")
        return

    msg = "🍀 **Summer Warehouse Jobs in Europe**\n\n"
    for i, job in enumerate(jobs, 1):
        msg += f"**{i}. {job['title']}**\n{job['link']}\n\n"

    requests.post(WEBHOOK, json={"content": msg})

# ---------------------------------------
# MAIN
# ---------------------------------------

def main():
    seen = load_seen()
    jobs = fetch_jooble()

    print(f"[DEBUG] Jooble returned: {len(jobs)} jobs")

    scored = []

    for job in jobs:
        if not job["id"]:
            continue

        if job["id"] in seen:
            continue

        score = score_job(job)

        if score >= 5:
            scored.append((score, job))
            seen.add(job["id"])

    scored.sort(reverse=True, key=lambda x: x[0])
    best = [job for score, job in scored[:MAX_RESULTS]]

    save_seen(seen)
    send_to_discord(best)

    print(f"Jobs sent: {len(best)}")

if __name__ == "__main__":
    main()
