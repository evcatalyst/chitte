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
    print(f"Config loaded.")
    return config


def build_prompt(config):
    region = config.get("region", "New York's Capital District")
    timeframe = config.get("timeframe", "next 60 days")
    sources = ", ".join(config.get("sources", []))
    predilections = "; ".join(config.get("user_predilections", []))

    # Tight, verifiability-focused instructions
    prompt = (
        f"Aggregate upcoming events for {region} from these sources (use the exact URLs): {sources}. "
        f"Timeframe: {timeframe}. "
        f"Instructions: {config.get('instructions', '')} "
        f"User predilections: {predilections}. "
        f"Branding: {config.get('branding', '')} "
        "Rules: Only include events that you can verify on public web pages; each event must include a valid http(s) URL in the 'link' field. "
        "Include exact source URLs (http or https) in the 'sources' array. "
        "Return strictly a JSON object with 'events' (array) and 'sources' (array) following the provided schema; no extra commentary."
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
    model = config.get("model", "grok-3-mini")
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

    print(f"Calling API model={model} ...")
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=90)
        print(f"API response status: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        if not content:
            raise ValueError("Empty content from API.")

        try:
            result = json.loads(content)
        except Exception:
            match = re.search(r'({.*})', content, re.DOTALL)
            if match:
                result = json.loads(match.group(1))
            else:
                raise ValueError("No valid JSON found in API response content.")

        return result
    except Exception as e:
        print(f"Error calling API with model {model}: {e}")
        # Optional fallback to a larger model if configured differently
        if model != "grok-3":
            try:
                print("Retrying with model grok-3 ...")
                payload["model"] = "grok-3"
                resp = requests.post(API_URL, headers=headers, json=payload, timeout=90)
                print(f"API response status: {resp.status_code}")
                resp.raise_for_status()
                data = resp.json()
                content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
                if not content:
                    raise ValueError("Empty content from API (fallback).")
                try:
                    result = json.loads(content)
                except Exception:
                    match = re.search(r'({.*})', content, re.DOTALL)
                    if match:
                        result = json.loads(match.group(1))
                    else:
                        raise ValueError("No valid JSON found in API response content (fallback).")
                return result
            except Exception as e2:
                print(f"Fallback call failed: {e2}")
        raise


def is_http_url(url):
    if not isinstance(url, str):
        return False
    u = url.strip()
    return u.startswith("http://") or u.startswith("https://")


def parse_date(date_str):
    if not isinstance(date_str, str):
        return None
    s = date_str.strip()
    # Try common formats
    fmts = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%m/%d/%Y",
        "%b %d, %Y",    # Jan 02, 2025
        "%B %d, %Y",    # January 02, 2025
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.date()
        except Exception:
            pass
    # Last resort: just YYYY-MM-DD from start if present
    m = re.match(r"^\s*(\d{4}-\d{2}-\d{2})", s)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except Exception:
            pass
    return None


def get_horizon_days(config):
    tf = config.get("timeframe", "")
    # Extract an integer number of days if present, default to 60
    nums = re.findall(r"(\d+)", str(tf))
    if nums:
        try:
            return int(nums[-1])
        except Exception:
            pass
    return 60


def coerce_venue_info(obj):
    # Ensure venue_info object with required keys; accept empty strings if not provided
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


def validate_and_normalize(raw, horizon_days):
    today = date.today()
    max_day = today + timedelta(days=horizon_days)

    events_in = raw.get("events", []) if isinstance(raw, dict) else []
    sources_in = raw.get("sources", []) if isinstance(raw, dict) else []

    # Normalize sources: allow strings or {title,url}
    sources_out = []
    for s in sources_in:
        if isinstance(s, str):
            title = s.strip()
            url = title  # if string is a URL, keep; otherwise drop later
            if is_http_url(url):
                sources_out.append({"title": title, "url": url})
        elif isinstance(s, dict):
            title = str(s.get("title", "")).strip()
            url = str(s.get("url", "")).strip()
            if title and is_http_url(url):
                sources_out.append({"title": title, "url": url})
        # Drop anything without a valid http(s) url

    events_out = []
    for e in events_in:
        if not isinstance(e, dict):
            continue

        date_str = e.get("date")
        d = parse_date(date_str)
        if not d:
            continue
        if d < today or d > max_day:
            continue

        venue = str(e.get("venue", "")).strip()
        desc = str(e.get("description", "")).strip()
        category = str(e.get("category", "")).strip()
        link = e.get("link", "")
        # time may be optional; normalize to "TBD" if missing/empty
        t = str(e.get("time", "")).strip() or "TBD"

        if not (venue and desc and category and is_http_url(link)):
            continue

        is_new = bool(e.get("is_new", False))
        venue_info = coerce_venue_info(e.get("venue_info", {}))

        events_out.append({
            "date": d.isoformat(),
            "time": t,
            "venue": venue,
            "description": desc,
            "category": category,
            "is_new": is_new,
            "link": link.strip(),
            "venue_info": venue_info
        })

    return {
        "events": events_out,
        "sources": sources_out
    }


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
        prompt = build_prompt(config)
        raw = call_grok_api(prompt, config)
        horizon = get_horizon_days(config)
        validated = validate_and_normalize(raw, horizon)
        if len(validated["events"]) == 0:
            print("No valid events after validation. Not updating events.json.")
            sys.exit(1)
        save_events(validated)
        print("Done.")
    except SystemExit as se:
        raise
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()