from __future__ import annotations

from io import StringIO
from unittest import TestCase
from slypilot.runtime.execution_events import EventStatus
from slypilot.runtime.execution_timeline import ExecutionTimeline
from slypilot.ui.timeline_renderer import TimelineRenderer


class TimelineRendererTests(TestCase):
    def test_render_compact_summary(self) -> None:
        buffer = StringIO()
        renderer = TimelineRenderer(output_func=buffer.write, verbose=False)
        timeline = ExecutionTimeline()
        timeline.emit("PROJECT_DETECTED", "Détection", status=EventStatus.SUCCESS)
        
        renderer.render_compact_summary(timeline)
        output = buffer.getvalue().lower()
        self.assertIn("travail effectué", output)
        self.assertIn("projet détecté", output)
        self.assertIn("›", output)

    def test_render_compact_summary_multiple(self) -> None:
        buffer = StringIO()
        renderer = TimelineRenderer(output_func=buffer.write, verbose=False)
        timeline = ExecutionTimeline()
        timeline.emit("PROJECT_DETECTED", "Détection", status=EventStatus.SUCCESS)
        timeline.emit("CARTOGRAPHY_LOADED", "Carto", status=EventStatus.SUCCESS)
        
        renderer.render_compact_summary(timeline)
        output = buffer.getvalue().lower()
        self.assertIn("projet détecté • cartographie chargée", output)

    def test_render_event_prefixes(self) -> None:
        buffer = StringIO()
        renderer = TimelineRenderer(output_func=buffer.write, verbose=True)
        timeline = ExecutionTimeline()
        event = timeline.emit("TEST", "Action", status=EventStatus.SUCCESS)
        renderer.render_event(event)
        output = buffer.getvalue()
        self.assertIn("✓ Action", output)
        
        buffer = StringIO()
        renderer = TimelineRenderer(output_func=buffer.write, verbose=True)
        event = timeline.emit("TEST", "Action", status=EventStatus.RUNNING)
        renderer.render_event(event)
        output = buffer.getvalue()
        self.assertIn("⏳ Action", output)
