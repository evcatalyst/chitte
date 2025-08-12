import os
import sys
import json
import re
import requests
from datetime import datetime, timedelta, date

CONFIG_PATH = "config_logic.json"
EVENTS_PATH = "events.json"
API_URL = "https://api.x.ai/v1/chat/completions"
API_KEY = os.getenv("GROK_API_KEY")


def load_config():
    print(f"Loading config from {CONFIG_PATH}...")
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    print("Config loaded.")
    return config


def load_previous_events():
    """Load previous events.json if exists to determine is_new status."""
    try:
        with open(EVENTS_PATH, "r") as f:
            data = json.load(f)
        events = data.get("events", [])
        # Create a set of event tuples for fast lookup
        previous_events = set()
        for event in events:
            key = (event.get("date"), event.get("venue"), event.get("description"))
            previous_events.add(key)
        print(f"Loaded {len(events)} previous events for comparison.")
        return previous_events, events
    except (FileNotFoundError, json.JSONDecodeError):
        print("No previous events.json found or invalid JSON.")
        return set(), []


def build_prompt(config):
    region = config.get("region", "New York's Capital District")
    timeframe = config.get("timeframe", "next 60 days")
    sources = ", ".join(config.get("sources", []))
    predilections = "; ".join(config.get("user_predilections", []))

    prompt = (
        f"Aggregate upcoming events for {region} from these sources (use the exact URLs): {sources}. "
        f"Timeframe: {timeframe}. "
        f"Instructions: {config.get('instructions', '')} "
        f"User predilections: {predilections}. "
        f"Branding: {config.get('branding', '')} "
        "Return strictly a JSON object with 'events' (array) and 'sources' (array); no extra commentary."
    )
    print("Prompt built.")
    return prompt


def call_grok_api(prompt, config):
    if not API_KEY:
        raise RuntimeError("GROK_API_KEY environment variable is not set.")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    model = "grok-3"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert event aggregator. Return only valid JSON as specified."},
            {"role": "user", "content": prompt}
        ],
        "temperature": config.get("temperature", 0.3),
        "stream": False,
        "response_format": {"type": "json_object"}
    }
    if "max_tokens" in config:
        payload["max_tokens"] = config["max_tokens"]

    if os.getenv("DEBUG_EVENTS", ""):
        print("[DEBUG] Prompt:", prompt)
        print("[DEBUG] API payload:", json.dumps(payload, indent=2))
    print(f"Calling API model={model} ...")
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=90)
    if os.getenv("DEBUG_EVENTS", ""):
        print("[DEBUG] API response status:", resp.status_code)
        print("[DEBUG] API response text:", resp.text)
    else:
        print(f"API response status: {resp.status_code}")
    resp.raise_for_status()
    data = resp.json()
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise ValueError("Empty content from API.")

    try:
        return json.loads(content)
    except Exception:
        match = re.search(r'({.*})', content, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise ValueError("No valid JSON found in API response content.")


def is_http_url(url):
    if not isinstance(url, str):
        return False
    u = url.strip()
    return u.startswith("http://") or u.startswith("https://")


def parse_date(date_str):
    if not isinstance(date_str, str):
        return None
    s = date_str.strip()

    # ISO formats with optional Z or timezone offsets
    try:
        iso = s.replace("Z", "+00:00") if s.endswith("Z") else s
        return datetime.fromisoformat(iso).date()
    except Exception:
        pass

    # Remove weekday prefix like "Thu, "
    if "," in s and len(s.split(",", 1)[0].strip()) <= 10:
        s_wo_wd = s.split(",", 1)[1].strip()
    else:
        s_wo_wd = s

    fmts = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y",
        "%b %d, %Y",     # Jan 02, 2025
        "%B %d, %Y",     # January 02, 2025
        "%a, %b %d, %Y", # Thu, Aug 15, 2025
        "%a, %B %d, %Y"  # Thu, August 15, 2025
    ]
    for candidate in (s, s_wo_wd):
        for fmt in fmts:
            try:
                return datetime.strptime(candidate, fmt).date()
            except Exception:
                continue

    # Fallback: extract YYYY-MM-DD anywhere
    m = re.search(r'(\d{4}-\d{2}-\d{2})', s)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except Exception:
            return None
    return None


def get_horizon_days(config):
    tf = config.get("timeframe", "")
    nums = re.findall(r"(\d+)", str(tf))
    if nums:
        try:
            return int(nums[-1])
        except Exception:
            pass
    return 60


def coerce_venue_info(obj):
    default = {
        "yelp_url": "",
        "maps_url": "",
        "photo_url": "",
        "description": ""
    }
    if not isinstance(obj, dict):
        return default
    out = {}
    for k in default:
        v = obj.get(k, "")
        if k.endswith("_url"):
            out[k] = v if is_http_url(v) else ""
        else:
            out[k] = v if isinstance(v, str) else ""
    return out


def validate_and_normalize(raw, horizon_days, previous_events=None):
    if previous_events is None:
        previous_events = set()
        
    today = date.today()
    max_day = today + timedelta(days=horizon_days)

    events_in = raw.get("events", []) if isinstance(raw, dict) else []
    sources_in = raw.get("sources", []) if isinstance(raw, dict) else []
    
    # Counters for logging
    total_events = len(events_in)
    skipped_invalid_date = 0
    skipped_out_of_window = 0
    skipped_missing_fields = 0

    # Normalize sources with readable titles
    def extract_title_from_url(url):
        if not is_http_url(url):
            return url
        # Extract domain and use as title
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            domain = match.group(1)
            # Map known domains to site names
            domain_map = {
                "albany.com": "Albany.com",
                "timesunion.com": "Times Union",
                "eventbrite.com": "Eventbrite",
                "empirestateplaza.ny.gov": "Empire State Plaza",
                "albanyinstitute.org": "Albany Institute of History & Art",
                "proctors.org": "Proctors Theatre",
                "theegg.org": "The Egg",
                "palacealbany.org": "Palace Theatre",
                "troymusichall.org": "Troy Music Hall",
                "thecohoesmusichall.org": "Cohoes Music Hall"
            }
            return domain_map.get(domain, domain)
        return url

    sources_out = []
    for s in sources_in:
        url = None
        title = None
        if isinstance(s, str):
            url = s.strip()
            title = extract_title_from_url(url)
        elif isinstance(s, dict):
            url = str(s.get("url", "")).strip()
            title = str(s.get("title", "")).strip() or extract_title_from_url(url)
        # Explicitly skip if url is missing, empty, or not valid
        if not url or not isinstance(url, str) or not url.strip() or not is_http_url(url):
            continue
        sources_out.append({"title": title, "url": url})

    events_out = []
    for e in events_in:
        if not isinstance(e, dict):
            continue

        d = parse_date(e.get("date"))
        if not d:
            skipped_invalid_date += 1
            continue
        if d < today or d > max_day:
            skipped_out_of_window += 1
            continue

        venue = str(e.get("venue", "")).strip()
        desc = str(e.get("description", "")).strip()
        category = str(e.get("category", "")).strip()
        link = e.get("link", "")
        t = str(e.get("time", "")).strip() or "TBD"

        if not (venue and desc and category and is_http_url(link)):
            skipped_missing_fields += 1
            continue

        # Determine is_new status
        event_key = (d.isoformat(), venue, desc)
        is_new = bool(e.get("is_new", False))
        if not is_new and event_key not in previous_events:
            is_new = True

        events_out.append({
            "date": d.isoformat(),
            "time": t,
            "venue": venue,
            "description": desc,
            "category": category,
            "is_new": is_new,
            "link": link.strip(),
            "venue_info": coerce_venue_info(e.get("venue_info", {}))
        })

    # Log validation stats
    if os.getenv("DEBUG_EVENTS", ""):
        print(f"[DEBUG] Validation stats: {total_events} total, {len(events_out)} valid, "
              f"{skipped_invalid_date} skipped (invalid date), "
              f"{skipped_out_of_window} skipped (out of window), "
              f"{skipped_missing_fields} skipped (missing fields)")
    else:
        print(f"Validation: {total_events} total → {len(events_out)} valid events")

    return {"events": events_out, "sources": sources_out}


def save_events(validated):
    payload = {
        "last_updated": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "events": validated["events"],
        "sources": validated["sources"]
    }
    with open(EVENTS_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {len(validated['events'])} events to {EVENTS_PATH}.")


def main():
    try:
        config = load_config()
        previous_events, previous_events_list = load_previous_events()
        prompt = build_prompt(config)
        raw = call_grok_api(prompt, config)
        horizon = get_horizon_days(config)
        validated = validate_and_normalize(raw, horizon, previous_events)
        
        # Always write debug files when DEBUG_EVENTS is set
        if os.getenv("DEBUG_EVENTS", ""):
            with open("last_run_raw.json", "w") as f:
                json.dump(raw, f, indent=2)
            with open("last_run_validated.json", "w") as f:
                json.dump(validated, f, indent=2)
            print("Wrote last_run_raw.json and last_run_validated.json for debugging.")
        
        if len(validated["events"]) == 0:
            print("No valid events after validation.")
            force_save = os.getenv("FORCE_SAVE_ON_EMPTY", "").lower() in ("1", "true", "yes")
            if force_save:
                print("FORCE_SAVE_ON_EMPTY is set, saving empty events.json with updated timestamp.")
                save_events(validated)
            else:
                print("Not updating events.json (use FORCE_SAVE_ON_EMPTY=1 to force save).")
                soft = bool(config.get("soft_fail_on_empty", True))
                sys.exit(0 if soft else 1)
        else:
            save_events(validated)
        print("Done.")
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: Fatal error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()