from __future__ import annotations
from typing import Callable
from ..runtime.execution_events import ExecutionEvent, EventStatus
from .style import dim

class TimelineRenderer:
    def __init__(self, output_func: Callable[[str], None] = print, verbose: bool = False) -> None:
        self.output = output_func
        self.verbose = verbose

    def render_event(self, event: ExecutionEvent) -> None:
        if not self.verbose:
            return
            
        icon = {
            EventStatus.RUNNING: "⏳",
            EventStatus.SUCCESS: "✓",
            EventStatus.WARNING: "⚠️",
            EventStatus.FAILED: "✗",
            EventStatus.SKIPPED: "⏭️",
        }.get(event.status, "•")
        
        prefix = "  ›"
        if event.status == EventStatus.SUCCESS:
             prefix = "  ✓"
        elif event.status == EventStatus.FAILED:
             prefix = "  ✗"
        elif event.status == EventStatus.RUNNING:
             prefix = "  ⏳"

        message = f"{prefix} {event.title}"
        if event.details:
            message += f" : {event.details}"
        
        self.output(dim(message))

    def render_compact_summary(self, timeline: "ExecutionTimeline") -> None:
        if self.verbose:
            return
            
        summary = timeline.get_summary()
        self.output(dim(f"› Travail effectué : {summary.lower()}"))
