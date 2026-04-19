from __future__ import annotations
from typing import List

from batchmark.pause import PauseState


def pause_state_to_dict(state: PauseState) -> dict:
    return {
        "commands_run": state.count,
        "pause_count": state.pause_count,
        "total_paused_seconds": round(state.total_paused, 4),
    }


def format_pause_json(state: PauseState) -> str:
    import json
    return json.dumps(pause_state_to_dict(state), indent=2)


def format_pause_table(state: PauseState) -> str:
    d = pause_state_to_dict(state)
    lines = [
        "Pause Summary",
        "-" * 30,
        f"Commands run    : {d['commands_run']}",
        f"Pauses inserted : {d['pause_count']}",
        f"Total paused    : {d['total_paused_seconds']}s",
    ]
    return "\n".join(lines)
