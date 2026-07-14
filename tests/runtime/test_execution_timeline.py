from __future__ import annotations

from io import StringIO
from contextlib import redirect_stdout
from unittest import TestCase

from slypilot.runtime.execution_events import ExecutionEvent, EventStatus
from slypilot.runtime.execution_timeline import ExecutionTimeline
from slypilot.ui.timeline_renderer import TimelineRenderer


class ExecutionTimelineTests(TestCase):
    def test_execution_event_to_dict(self) -> None:
        event = ExecutionEvent(
            event_type="TEST",
            title="Test Event",
            status=EventStatus.SUCCESS,
            details="All good",
            source="tester",
        )
        data = event.to_dict()
        self.assertEqual(data["event_type"], "TEST")
        self.assertEqual(data["title"], "Test Event")
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["details"], "All good")
        self.assertEqual(data["source"], "tester")
        self.assertIn("timestamp", data)

    def test_timeline_emit(self) -> None:
        events: list[ExecutionEvent] = []

        def on_event(e: ExecutionEvent) -> None:
            events.append(e)

        timeline = ExecutionTimeline(on_event=on_event)
        timeline.emit("START", "Starting process")

        self.assertEqual(len(timeline.events), 1)
        self.assertEqual(len(events), 1)
        self.assertEqual(timeline.events[0].event_type, "START")
        self.assertEqual(timeline.events[0].status, EventStatus.RUNNING)

    def test_timeline_update(self) -> None:
        events: list[ExecutionEvent] = []

        def on_event(e: ExecutionEvent) -> None:
            events.append(e)

        timeline = ExecutionTimeline(on_event=on_event)
        event = timeline.emit("START", "Starting process")
        timeline.update_event(event, EventStatus.SUCCESS, details="Done")

        self.assertEqual(len(events), 2)
        self.assertEqual(event.status, EventStatus.SUCCESS)
        self.assertEqual(event.details, "Done")

    def test_timeline_renderer(self) -> None:
        buffer = StringIO()
        renderer = TimelineRenderer(output_func=buffer.write, verbose=True)
        event = ExecutionEvent("TEST", "Test Title", EventStatus.SUCCESS, details="Test Details")
        renderer.render_event(event)
        self.assertIn("✓ Test Title : Test Details", buffer.getvalue())

    def test_timeline_renderer_running(self) -> None:
        buffer = StringIO()
        renderer = TimelineRenderer(output_func=buffer.write, verbose=True)
        event = ExecutionEvent("TEST", "Test Title", EventStatus.RUNNING)
        renderer.render_event(event)
        self.assertIn("⏳ Test Title", buffer.getvalue())

    def test_timeline_get_summary(self) -> None:
        timeline = ExecutionTimeline()
        timeline.emit("PROJECT_DETECTED", "Détection", status=EventStatus.SUCCESS)
        timeline.emit("CARTOGRAPHY_LOADED", "Carto", status=EventStatus.SUCCESS)
        
        summary = timeline.get_summary()
        self.assertEqual(summary, "Projet détecté • Cartographie chargée")

    def test_timeline_renderer_compact_vs_verbose(self) -> None:
        # Verbose mode
        buffer = StringIO()
        verbose_renderer = TimelineRenderer(output_func=buffer.write, verbose=True)
        event = ExecutionEvent("TEST", "Test Title", EventStatus.SUCCESS)
        verbose_renderer.render_event(event)
        verbose_renderer.render_compact_summary(ExecutionTimeline())
        
        output = buffer.getvalue()
        self.assertIn("✓ Test Title", output)
        self.assertNotIn("Travail effectué", output)

        # Compact mode
        buffer = StringIO()
        compact_renderer = TimelineRenderer(output_func=buffer.write, verbose=False)
        timeline = ExecutionTimeline()
        timeline.emit("PROJECT_DETECTED", "Détection", status=EventStatus.SUCCESS)
        event = ExecutionEvent("TEST", "Test Title", EventStatus.SUCCESS)
        compact_renderer.render_event(event)
        compact_renderer.render_compact_summary(timeline)
        
        output = buffer.getvalue().lower()
        self.assertNotIn("✓ test title", output)
        self.assertIn("travail effectué : projet détecté", output)
