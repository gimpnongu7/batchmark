"""Matrix runner: run commands across multiple variable substitutions."""
from dataclasses import dataclass, field
from typing import Dict, List, Any
from batchmark.runner import CommandResult, run_command


@dataclass
class MatrixEntry:
    command_template: str
    variables: Dict[str, Any]
    result: CommandResult

    @property
    def rendered_command(self) -> str:
        return self.command_template.format(**self.variables)


@dataclass
class MatrixConfig:
    commands: List[str]
    matrix: Dict[str, List[Any]]
    timeout: float = 30.0


def _expand_matrix(matrix: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """Cartesian product of all matrix variable lists."""
    keys = list(matrix.keys())
    if not keys:
        return [{}]
    combos: List[Dict[str, Any]] = [{}]
    for key in keys:
        new_combos = []
        for combo in combos:
            for val in matrix[key]:
                new_combos.append({**combo, key: val})
        combos = new_combos
    return combos


def run_matrix(config: MatrixConfig) -> List[MatrixEntry]:
    """Run each command template for every variable combination."""
    entries: List[MatrixEntry] = []
    combos = _expand_matrix(config.matrix)
    for template in config.commands:
        for variables in combos:
            cmd = template.format(**variables)
            result = run_command(cmd, timeout=config.timeout)
            entries.append(MatrixEntry(
                command_template=template,
                variables=variables,
                result=result,
            ))
    return entries


def format_matrix_table(entries: List[MatrixEntry]) -> str:
    lines = [f"{'COMMAND':<50} {'VARS':<30} {'STATUS':<10} {'DURATION':>10}"]
    lines.append("-" * 104)
    for e in entries:
        vars_str = ",".join(f"{k}={v}" for k, v in e.variables.items())
        lines.append(
            f"{e.rendered_command:<50} {vars_str:<30} {e.result.status:<10} {e.result.duration:>9.3f}s"
        )
    return "\n".join(lines)
