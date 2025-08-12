# Chitte à Dou

## Overview
Chitte à Dou is an automated event aggregation site for New York's Capital District, powered by AI (Grok API) and hosted on GitHub Pages. It fetches events from multiple sources, outputs them in a structured JSON format, and renders them in a minimalist, multi-theme front-end.

## How the Pipeline Works
1. **Configuration**: The pipeline uses `config_logic.json` to define sources, prompts, and user preferences for event aggregation.
2. **Automation**: GitHub Actions (`update-events.yml`) runs the Python script (`script.py`) daily and on manual dispatch.
3. **Event Aggregation**: The script calls the Grok API, passing a prompt built from the config, and expects a JSON response with an array of events and sources.
4. **Front-End**: The static site (`index.html`, `custom.css`, `script.js`) fetches `events.json` and renders the events table with interactive features.

## Automation Workflow

The site automatically updates daily at 5:00 AM UTC via GitHub Actions. The workflow:

1. **Triggers**: Runs daily at 5 AM UTC or manually via "Run workflow" button
2. **Event Generation**: Runs `script.py` with debug mode enabled (`DEBUG_EVENTS=1`)
3. **Testing**: Validates the generated `events.json` with unit tests
4. **Smart Updates**: Only commits changes if `events.json` or debug files have changed
5. **Debug Artifacts**: Uploads raw API responses and validated data as downloadable artifacts

### Required Secrets
- `GROK_API_KEY`: Your Grok API key for event aggregation

### Manual Dispatch
Go to Actions → "Update Events" → "Run workflow" to manually trigger event updates.

### Debug Artifacts
When the workflow runs, it creates debug files:
- `last_run_raw.json`: Raw API response 
- `last_run_validated.json`: Events after validation/filtering
These are uploaded as workflow artifacts for troubleshooting.

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

## Troubleshooting

### Only Getting One Event or No Events
- **Sources**: Make sure your `sources` array in `config_logic.json` is comprehensive and includes active event sites
- **Timeframe**: Set a longer `timeframe` (e.g., "next 90 days") to capture more events
- **API Issues**: Check the workflow logs in GitHub Actions for API errors or quota issues
- **Debug Mode**: Enable `DEBUG_EVENTS=1` locally to see raw API responses and validation details

### Empty Results Handling
- **Default Behavior**: Empty results don't update `events.json` (preserves existing events)
- **Force Save**: Set `FORCE_SAVE_ON_EMPTY=1` to save empty `events.json` with updated timestamp (useful to signal pipeline freshness)
- **Soft Fail**: The pipeline uses `soft_fail_on_empty=true` by default (exit code 0 for empty results)

### "New Event" Detection
Events are automatically marked `is_new=true` if they weren't in the previous `events.json`:
- **Comparison**: Based on exact match of (date, venue, description) 
- **Manual Override**: API can still explicitly set `is_new=true/false` to override detection
- **Fresh Installs**: All events are marked `is_new=true` when no previous `events.json` exists

### Common Issues
- **Network Errors**: Retry the workflow or check Grok API status
- **JSON Parse Errors**: Usually indicates malformed API response - check debug artifacts
- **Validation Failures**: Events missing required fields (venue, description, category, valid link) are filtered out

## Manual Run
You can manually trigger the workflow in the GitHub Actions tab by clicking "Run workflow" on `Update Events`.

## Customization
- **Themes**: Edit `custom.css` to add or tweak themes.
- **Front-End**: Modify `index.html` and `script.js` for new features or layout changes.

## Contact
For issues or feature requests, open an issue in the GitHub repository.

---

**Tip:** The more specific and comprehensive your config, the better the event coverage. Regularly review and update your sources and preferences for best results.
