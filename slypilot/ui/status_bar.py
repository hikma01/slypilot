"""Real-time execution status bar for SlyPilot CLI."""

from __future__ import annotations

import sys
import time
import threading
from typing import Callable
from .style import dim


class StatusBar:
    def __init__(self, output_func: Callable[[str], None] = sys.stdout.write) -> None:
        self.output = output_func
        self._current_step = ""
        self._start_time = 0.0
        self._active = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def start(self, initial_step: str = "initialisation") -> None:
        """Start the status bar timer and background update thread."""
        with self._lock:
            if self._active:
                return
            self._active = True
            self._current_step = initial_step
            self._start_time = time.time()
            self._stop_event.clear()
            
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def update(self, step_name: str) -> None:
        """Update the current execution step name."""
        with self._lock:
            self._current_step = step_name

    def stop(self) -> None:
        """Stop the status bar and clear it from the terminal."""
        with self._lock:
            if not self._active:
                return
            self._stop_event.set()
            self._active = False
            
        if self._thread:
            self._thread.join()
        
        # Clear the line
        self.output("\r" + " " * 80 + "\r")
        sys.stdout.flush()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            elapsed = int(time.time() - self._start_time)
            with self._lock:
                step = self._current_step
            
            # Format: • Working (12s) · étape : chargement cartographie · ctrl+c to interrupt
            # Note: esc to interrupt is harder to catch globally in Python CLI, 
            # using ctrl+c text as it's the standard.
            message = f"• Working ({elapsed}s) · étape : {step} · ctrl+c to interrupt"
            
            # Write to stdout with carriage return to overwrite
            line = "\r" + dim(message)
            self.output(line)
            sys.stdout.flush()
            
            time.sleep(0.5)
