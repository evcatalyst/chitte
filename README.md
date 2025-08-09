# Chitte à Dou

## Overview
Chitte à Dou is an automated event aggregation site for New York's Capital District, powered by AI (Grok API) and hosted on GitHub Pages. It fetches events from multiple sources, outputs them in a structured JSON format, and renders them in a minimalist, multi-theme front-end.

## How the Pipeline Works
1. **Configuration**: The pipeline uses `config_logic.json` to define sources, prompts, and user preferences for event aggregation.
2. **Automation**: GitHub Actions (`update-events.yml`) runs the Python script (`script.py`) daily and on manual dispatch.
3. **Event Aggregation**: The script calls the Grok API, passing a prompt built from the config, and expects a JSON response with an array of events and sources.
4. **Front-End**: The static site (`index.html`, `custom.css`, `script.js`) fetches `events.json` and renders the events table with interactive features.

## Configuration: `config_logic.json`
- **sources**: List of event sources to aggregate from. Add more reputable sources for broader coverage.
- **instructions**: Guidance for the AI on what to include/exclude (e.g., avoid ads, focus on quality events).
- **user_predilections**: Array of preferences to filter events (e.g., focus on music, exclude commercial events).
- **branding**: Branding instructions for the output (e.g., "New Chitte" badge for recent events).
- **json_schema**: Defines the expected output format.

### Example: Adding More Sources
Edit `config_logic.json` and expand the `sources` array:
```json
"sources": [
  "Albany.com events calendar",
  "Times Union weekly picks",
  "Eventbrite for Capital District",
  "Empire State Plaza site",
  "Schenectady County Tourism",
  "Troy Night Out",
  "Saratoga.com events",
  "Local music venues (e.g., The Hollow, Putnam Place)",
  "Community calendars (libraries, parks)"
]
```

### Example: Expanding Timeframe
You can adjust the `timeframe` field to cover more days:
```json
"timeframe": "Upcoming events for the next 30 days, starting from current date."
```

## Troubleshooting: Only One Event
- Make sure your `sources` array in `config_logic.json` is comprehensive.
- Set a longer `timeframe`.
- Ensure your Grok API key is valid and has quota.
- Check the workflow logs in GitHub Actions for errors.
- The AI may sometimes return limited results; try re-running the workflow or refining the prompt.

## Manual Run
You can manually trigger the workflow in the GitHub Actions tab by clicking "Run workflow" on `Update Events`.

## Customization
- **Themes**: Edit `custom.css` to add or tweak themes.
- **Front-End**: Modify `index.html` and `script.js` for new features or layout changes.

## Contact
For issues or feature requests, open an issue in the GitHub repository.

---

**Tip:** The more specific and comprehensive your config, the better the event coverage. Regularly review and update your sources and preferences for best results.
