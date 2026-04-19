from dataclasses import dataclass, field
from typing import Callable, Optional
import sys
import time


@dataclass
class ProgressConfig:
    enabled: bool = True
    stream: object = field(default_factory=lambda: sys.stderr)
    show_elapsed: bool = True
    bar_width: int = 30


@dataclass
class ProgressState:
    total: int
    completed: int = 0
    start_time: float = field(default_factory=time.monotonic)

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.start_time

    @property
    def percent(self) -> float:
        if self.total == 0:
            return 1.0
        return self.completed / self.total


def _render_bar(state: ProgressState, width: int) -> str:
    filled = int(state.percent * width)
    bar = "#" * filled + "-" * (width - filled)
    pct = int(state.percent * 100)
    return f"[{bar}] {pct}% ({state.completed}/{state.total})"


def render_progress(state: ProgressState, cfg: ProgressConfig) -> str:
    bar = _render_bar(state, cfg.bar_width)
    if cfg.show_elapsed:
        bar += f"  {state.elapsed:.1f}s"
    return bar


def make_progress_callback(
    total: int,
    cfg: Optional[ProgressConfig] = None,
) -> Callable[[str], None]:
    cfg = cfg or ProgressConfig()
    if not cfg.enabled:
        return lambda cmd: None
    state = ProgressState(total=total)

    def callback(command: str) -> None:
        state.completed += 1
        line = render_progress(state, cfg)
        cfg.stream.write(f"\r{line}  cmd: {command[:40]:<40}")
        cfg.stream.flush()
        if state.completed == state.total:
            cfg.stream.write("\n")
            cfg.stream.flush()

    return callback
