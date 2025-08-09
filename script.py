import os
import json
import requests
from datetime import datetime

CONFIG_PATH = "config_logic.json"
EVENTS_PATH = "www/events.json"
API_URL = "https://api.x.ai/v1/chat/completions"
API_KEY = os.getenv("GROK_API_KEY")

def load_config():
    print(f"Loading config from {CONFIG_PATH}...")
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
    print(f"Config loaded: {json.dumps(config, indent=2)}")
    return config

def build_prompt(config):
    sources = ", ".join(config.get("sources", []))
    predilections = "; ".join(config.get("user_predilections", []))
    prompt = (
        f"Aggregate upcoming events for New York's Capital District (Albany, Schenectady, Troy, Saratoga, and surrounding areas) "
        f"from these sources: {sources}. "
        f"Timeframe: next 30 days from today. "
        f"Instructions: {config.get('instructions', '')} "
        f"User predilections: {predilections}. "
        f"Branding: {config.get('branding', '')} "
        f"Output strictly as JSON object with 'events' array and 'sources' array conforming to this schema; no extra text."
    )
    print(f"Prompt built: {prompt}")
    return prompt

def call_grok_api(prompt, config):
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
        "temperature": config.get("temperature", 0.7),
        "stream": False,
        "response_format": {"type": "json_object"}
    }
    print(f"Calling Grok API with payload: {json.dumps(payload, indent=2)}")
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        print(f"API response status: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        print(f"Raw API response: {json.dumps(data, indent=2)}")
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"API content: {content}")
        try:
            result = json.loads(content)
        except Exception:
            import re
            match = re.search(r'({.*})', content, re.DOTALL)
            if match:
                result = json.loads(match.group(1))
            else:
                print("No valid JSON found in API response content.")
                raise ValueError("No valid JSON found in API response.")
        print(f"Parsed result: {json.dumps(result, indent=2)}")
        return result
    except Exception as e:
        print(f"Error calling Grok API: {e}")
        if model != "grok-3":
            print("Retrying with grok-3...")
            payload["model"] = "grok-3"
            try:
                resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                print(f"API response status (grok-3): {resp.status_code}")
                resp.raise_for_status()
                data = resp.json()
                print(f"Raw API response (grok-3): {json.dumps(data, indent=2)}")
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"API content (grok-3): {content}")
                try:
                    result = json.loads(content)
                except Exception:
                    import re
                    match = re.search(r'({.*})', content, re.DOTALL)
                    if match:
                        result = json.loads(match.group(1))
                    else:
                        print("No valid JSON found in API response content (grok-3).")
                        raise ValueError("No valid JSON found in API response.")
                print(f"Parsed result (grok-3): {json.dumps(result, indent=2)}")
                return result
            except Exception as e2:
                print(f"Error calling Grok API with grok-3: {e2}")
        return None

def save_events(data):
    print(f"Saving events to {EVENTS_PATH}...")
    data["last_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(EVENTS_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Events saved: {json.dumps(data, indent=2)}")

def main():
    if not API_KEY:
        print("Missing GROK_API_KEY environment variable.")
        return
    config = load_config()
    prompt = build_prompt(config)
    data = call_grok_api(prompt, config)
    if data and "events" in data and "sources" in data:
        print(f"Events found: {len(data['events'])}, Sources found: {len(data['sources'])}")
        save_events(data)
        print("Events updated successfully.")
    else:
        print("Failed to update events. Check API response and config.")

if __name__ == "__main__":
    main()
