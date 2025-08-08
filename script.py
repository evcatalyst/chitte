import os
import json
import requests
from datetime import datetime

CONFIG_PATH = "config_logic.json"
EVENTS_PATH = "events.json"
API_URL = "https://api.x.ai/v1/chat"
API_KEY = os.getenv("GROK_API_KEY")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def build_prompt(config):
    sources = ", ".join(config.get("sources", []))
    predilections = "; ".join(config.get("user_predilections", []))
    prompt = (
        f"Aggregate upcoming events for New York's Capital District (Albany, Schenectady, Troy, Saratoga, and surrounding areas) "
        f"from these sources: {sources}. "
        f"Timeframe: next 7-14 days from today. "
        f"Instructions: {config.get('instructions', '')} "
        f"User predilections: {predilections}. "
        f"Branding: {config.get('branding', '')} "
        f"Output strictly as JSON object with 'events' array and 'sources' array conforming to this schema; no extra text."
    )
    return prompt

def call_grok_api(prompt, config):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config.get("model", "grok-4"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": config.get("temperature", 0.7),
        "max_tokens": config.get("max_tokens", 2048)
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Extract JSON from response (may be in 'choices' or 'content')
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Try to parse JSON from content
        try:
            result = json.loads(content)
        except Exception:
            # Fallback: find first JSON object in content
            import re
            match = re.search(r'({.*})', content, re.DOTALL)
            if match:
                result = json.loads(match.group(1))
            else:
                raise ValueError("No valid JSON found in API response.")
        return result
    except Exception as e:
        print(f"Error calling Grok API: {e}")
        return None

def save_events(data):
    # Add last updated field
    data["last_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(EVENTS_PATH, "w") as f:
        json.dump(data, f, indent=2)

def main():
    if not API_KEY:
        print("Missing GROK_API_KEY environment variable.")
        return
    config = load_config()
    prompt = build_prompt(config)
    data = call_grok_api(prompt, config)
    if data and "events" in data and "sources" in data:
        save_events(data)
        print("Events updated successfully.")
    else:
        print("Failed to update events. Check API response and config.")

if __name__ == "__main__":
    main()
