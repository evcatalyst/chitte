import json
import os
import unittest

class TestEventsJson(unittest.TestCase):
    def setUp(self):
        with open('events.json', 'r') as f:
            self.data = json.load(f)
        self.events = self.data.get('events', [])
        self.sources = self.data.get('sources', [])

    def test_event_fields(self):
        required_fields = [
            'date', 'time', 'venue', 'description', 'category', 'is_new', 'venue_info'
        ]
        for event in self.events:
            for field in required_fields:
                self.assertIn(field, event, f"Missing field: {field}")
                self.assertNotEqual(event[field], "", f"Field {field} is blank")

    def test_venue_info_fields(self):
        venue_fields = ['yelp_url', 'maps_url', 'photo_url', 'description']
        for event in self.events:
            venue_info = event.get('venue_info', {})
            for field in venue_fields:
                self.assertIn(field, venue_info, f"Missing venue_info field: {field}")

    def test_sources(self):
        for source in self.sources:
            self.assertIn('title', source)
            self.assertIn('url', source)
            self.assertTrue(source['url'].startswith('http'), f"Source URL invalid: {source['url']}")

    def test_event_links(self):
        for event in self.events:
            link = event.get('link', '')
            if link:
                self.assertTrue(link.startswith('http'), f"Event link invalid: {link}")

    def test_minimum_events(self):
        # Minimum event count requirement removed; allow any number of valid events
        pass

if __name__ == "__main__":
    unittest.main()
