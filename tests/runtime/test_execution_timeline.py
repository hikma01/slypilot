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
        renderer = TimelineRenderer()
        event = ExecutionEvent("TEST", "Test Title", EventStatus.SUCCESS, details="Test Details")
        buffer = StringIO()
        with redirect_stdout(buffer):
            renderer.render_event(event)

        self.assertIn("✓ Test Title : Test Details", buffer.getvalue())

    def test_timeline_renderer_running(self) -> None:
        renderer = TimelineRenderer()
        event = ExecutionEvent("TEST", "Test Title", EventStatus.RUNNING)
        buffer = StringIO()
        with redirect_stdout(buffer):
            renderer.render_event(event)

        self.assertIn("⏳ Test Title", buffer.getvalue())
