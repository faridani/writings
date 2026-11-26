#!/usr/bin/env python3
"""Build the Lean companion, audit its proofs, and check the article boxes.

Run from any directory after `lake exe cache get` in this project:
    python riemann/lean/verify.py
An explicit Lake executable can be supplied with --lake /path/to/lake.
Only Python's standard library is required by this verification driver.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


HERE = Path(__file__).resolve().parent
ARTICLE = HERE.parent.parent / "Riemann.md"


def article_blocks(text: str) -> list[dict]:
    blocks = []
    section = "Introduction"
    fence = None
    current = []
    start = 0
    for number, line in enumerate(text.splitlines(), 1):
        if fence is None:
            if line.startswith("## "):
                section = line.removeprefix("## ")
            match = re.fullmatch(r"(`{3,}|~{3,})lean\s*", line)
            if match:
                fence, current, start = match[1], [], number + 1
        elif line.strip() == fence:
            if not current or len(current) > 10:
                raise ValueError(f"Lean block at article line {start} has {len(current)} lines.")
            blocks.append({"section": section, "start_line": start,
                           "line_count": len(current), "code": "\n".join(current)})
            fence = None
        else:
            current.append(line)
    if fence is not None:
        raise ValueError("Unclosed Lean fence in the article.")
    if not blocks:
        raise ValueError("No Lean boxes found in the article.")
    for number in range(1, 15):
        if not any(b["section"].startswith(f"{number}. ") for b in blocks):
            raise ValueError(f"No Lean example in numbered section {number}.")
    return blocks


def run_checked(label: str, command: list[str], env: dict[str, str]) -> str:
    print(f"Checking {label}...", flush=True)
    result = subprocess.run(command, cwd=HERE, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        print(result.stdout, flush=True)
        raise RuntimeError(f"{label} failed with exit code {result.returncode}.")
    if re.search(r"declaration uses ['`]sorry|\bsorryAx\b", result.stdout):
        raise RuntimeError(f"{label} reported an unfinished proof:\n{result.stdout}")
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lake", default=shutil.which("lake"))
    args = parser.parse_args()
    if not args.lake:
        parser.error("Lake was not found. Install the pinned Lean toolchain, or use --lake.")
    lake = str(Path(args.lake).resolve())
    env = os.environ.copy()
    env["PATH"] = str(Path(lake).parent) + os.pathsep + env.get("PATH", "")
    blocks = article_blocks(ARTICLE.read_text())
    generated = HERE / ".lake" / "ArticleSnippets.lean"
    generated.parent.mkdir(exist_ok=True)
    # The opening article box supplies the imports and open declarations.
    generated.write_text("\n\n".join(
        f"-- Article line {b['start_line']}: {b['section']}\n{b['code']}" for b in blocks
    ) + "\n")
    build_output = run_checked("all companion modules", [lake, "build"], env)
    audit_output = run_checked("transitive proof axioms", [lake, "env", "lean", "Audit.lean"], env)
    snippet_output = run_checked("every article Lean box",
                                 [lake, "env", "lean", str(generated)], env)
    version = run_checked("compiler version", [lake, "env", "lean", "--version"], env).strip()
    match = re.search(r"AUDIT PASSED: (\d+) theorem declarations", audit_output)
    if not match:
        raise RuntimeError("The axiom audit did not report success.")
    manifest = json.loads((HERE / "lake-manifest.json").read_text())
    mathlib = next(p for p in manifest["packages"] if p["name"] == "mathlib")
    sources = [HERE / "Riemann.lean", HERE / "Audit.lean", *sorted((HERE / "Riemann").glob("*.lean")),
               HERE / "lean-toolchain", HERE / "lakefile.toml", HERE / "lake-manifest.json",
               HERE / "verify.py"]
    report = {
        "lean_version": version,
        "mathlib_revision": mathlib["rev"],
        "build_passed": True,
        "axiom_audit_passed": True,
        "theorem_declarations_audited": int(match[1]),
        "allowed_foundational_axioms": ["propext", "Quot.sound", "Classical.choice"],
        "article_snippets_compiled": len(blocks),
        "longest_article_lean_block_lines": max(b["line_count"] for b in blocks),
        "article_sha256": hashlib.sha256(ARTICLE.read_bytes()).hexdigest(),
        "article_blocks": [{k: v for k, v in b.items() if k != "code"} for b in blocks],
        "source_sha256": {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sources},
        "audit_output": audit_output.splitlines(),
        "build_output": build_output.splitlines(),
        "snippet_output": snippet_output.splitlines(),
        "scope": "Checks this pinned Lean project and all article Lean snippets. Does not prove RH, the analytic explicit formula, or correctness of the Python GIF calculations.",
    }
    path = HERE / "validation.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"PASS: {len(blocks)} article boxes, all at most 10 lines; "
          f"{match[1]} theorem declarations passed the axiom audit.")
    print(f"Validation report: {path}")


if __name__ == "__main__":
    main()
