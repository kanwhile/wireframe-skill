#!/usr/bin/env python3
"""Adversarial tests for skills/wireframe/scripts/self_check.py.

Both polarities, because a checker that never fires and a checker that fires on
everything are equally useless: each mutation must be caught, and each legal
case must stay silent. Run from the repository root:

    python3 scripts/test-self-check.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "wireframe" / "scripts"))

import self_check  # noqa: E402

BASE = """<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="utf-8" />
  <title>ระบบยืมครุภัณฑ์ — Product Wireframe</title>
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.2.4/dist/index.global.js"></script>
  <style>
    /* FLAT ONLY — no box-shadow and no gradient anywhere in this file. */
    html, body { background: #E8E8E8; color: #333333; line-height: 1.6; }
    .wf-callout { background: #1F1F1F; color: #fff; border: 2px solid #fff; }
    .wf-img { background: #F4F4F4 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0L100 100' stroke='%23BFBFBF'/%3E%3C/svg%3E"); }
    .chip { box-shadow: none; color: rgb(51, 51, 51); background: hsl(0, 0%, 96%); }
  </style>
</head>
<body>
  <main>
    <section id="tab-overview"><span>{{SURFACE}}สำรวจ · /app/*</span></section>
    <section id="tab-ia"><div class="mermaid">flowchart TD; A-->B</div></section>
    <section id="tab-flows"><div class="mermaid">sequenceDiagram; A->>B: ขอยืม</div></section>
    <section id="tab-screens" class="shadow-none">
      <img src="data:image/svg+xml,%3Csvg/%3E" alt="" />
    </section>
    <section id="tab-review"><button data-go="app-inbox">ไปที่คิว</button></section>
  </main>
  <script>
    const screens = {
      "app-inbox": {
        group: "App", label: "คิวรออนุมัติ", route: "/app/borrow-requests",
        why: "คิวทั้งสามอยู่หน้าเดียวเพราะเจ้าหน้าที่คนเดียวดูแลทั้งหมด (ADR 0001)",
        annotations: [
          { n: 1, tag: "behavior", text: "สถานะแท็บเก็บใน URL — รีเฟรชแล้วอยู่แท็บเดิม" },
          { n: 2, tag: "error",    text: "ถ้าของถูกยืมระหว่างรอ → red toast แล้วทั้งคำขอล้มเหลว" },
        ],
        html: () => `
          <div class="relative">
            ${[1, 2].map((i) => `<div class="skeleton">${i}</div>`).join("")}
            <span class="wf-callout" style="top:8px;left:8px">1</span>
            <span class="wf-callout" style="top:-8px;right:-8px">2</span>
          </div>`,
      },
    };
  </script>
</body>
</html>
"""


def run(source: str, **flags) -> tuple[list[str], list[str]]:
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as handle:
        handle.write(source)
        path = Path(handle.name)
    try:
        report = self_check.verify(
            path, flags.get("template", False), flags.get("artifact", False)
        )
        return report.errors, report.warnings
    finally:
        path.unlink()


CASES: list[tuple[str, str, str | None, dict]] = []


def must_fail(name: str, source: str, needle: str, **flags) -> None:
    CASES.append((name, source, needle, flags))


def must_pass(name: str, source: str, **flags) -> None:
    CASES.append((name, source, None, flags))


def swap(old: str, new: str, source: str = BASE) -> str:
    assert old in source, f"fixture anchor missing: {old!r}"
    return source.replace(old, new, 1)


CLEAN = swap("{{SURFACE}}", "")

# ── must not fire: the legal half ──────────────────────────────────────────
must_pass("clean fixture", CLEAN, template=True)
must_pass("clean fixture, non-template", CLEAN)
must_pass("route glob /app/* does not open a comment", CLEAN)
must_pass("hex grays, shadow-none, box-shadow: none, rgb/hsl grays", CLEAN)
must_pass("%23 gray inside a data URI", CLEAN)
must_pass("the word `red` inside annotation text", CLEAN)
must_pass("Thai body with lang=th", CLEAN)
must_pass("jsdelivr script outside Artifact mode", CLEAN)
must_pass("a comment naming box-shadow and gradient", CLEAN)
must_pass("data: image src", CLEAN)
must_pass("${...} interpolation inside the html template literal", CLEAN)
must_pass(
    "pre.mermaid and no remote asset in Artifact mode",
    swap(
        '<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.2.4/dist/index.global.js"></script>',
        "",
        CLEAN.replace('<div class="mermaid">', '<pre class="mermaid">').replace("</div>\n", "</pre>\n"),
    ).replace('<div class="mermaid">', '<pre class="mermaid">'),
    artifact=True,
)

# ── must fire: hue ─────────────────────────────────────────────────────────
must_fail("chromatic hex", swap("#1F1F1F", "#eb6c36", CLEAN), "hue found: #eb6c36")
must_fail("chromatic hex in a data URI", swap("%23BFBFBF", "%23EB6C36", CLEAN), "hue found: #EB6C36")
must_fail("named color", swap("color: #333333", "color: crimson", CLEAN), "named color `crimson`")
must_fail("tailwind hue utility", swap('class="relative"', 'class="relative bg-red-500"', CLEAN), "bg-red-500")
must_fail("tailwind hue on a variant", swap('class="skeleton"', 'class="skeleton hover:text-emerald-600"', CLEAN), "text-emerald-600")
must_fail("saturated hsl", swap("hsl(0, 0%, 96%)", "hsl(14, 82%, 56%)", CLEAN), "non-zero saturation")
must_fail("rgb with differing channels", swap("rgb(51, 51, 51)", "rgb(235, 108, 54)", CLEAN), "channels differ")

# ── must fire: flat ────────────────────────────────────────────────────────
must_fail("box-shadow", swap("box-shadow: none", "box-shadow: 0 2px 8px #0000001a", CLEAN), "box-shadow is not allowed")
must_fail("gradient", swap("background: #E8E8E8", "background: linear-gradient(#eee, #ddd)", CLEAN), "gradient is not allowed")
must_fail("shadow utility", swap('class="skeleton"', 'class="skeleton shadow-md"', CLEAN), "shadow-md")
must_fail("gradient utility", swap('class="relative"', 'class="relative bg-gradient-to-r"', CLEAN), "bg-gradient-to-r")

# ── must fire: content hygiene ─────────────────────────────────────────────
must_fail("lorem ipsum", swap("ไปที่คิว", "Lorem ipsum dolor", CLEAN), "Lorem ipsum")
must_fail("unreplaced placeholder", BASE, "unreplaced {{...}} placeholder")
must_fail("dark mode media query", swap("html, body {", "@media (prefers-color-scheme: dark) { body { color: #fff } }\n    html, body {", CLEAN), "no dark mode")
must_fail("dark: variant", swap('class="skeleton"', 'class="skeleton dark:bg-black"', CLEAN), "`dark:` variant")

# ── must fire: assets ──────────────────────────────────────────────────────
must_fail("google fonts", swap("<style>", '<link href="https://fonts.googleapis.com/css2?family=Inter" rel="stylesheet"><style>', CLEAN), "no Google Fonts link")
must_fail("external image", swap('src="data:image/svg+xml,%3Csvg/%3E"', 'src="https://example.com/hero.png"', CLEAN), "no real or external images")
must_fail("external css url()", swap('url("data:image/svg+xml', 'url("https://example.com/x.png") , url("data:image/svg+xml', CLEAN), "no external image")
must_fail("unexpected cdn host", swap("cdn.jsdelivr.net", "evil.example.com", CLEAN), "unexpected remote asset")
must_fail("remote asset in Artifact mode", CLEAN, "Artifact mode allows no remote asset", artifact=True)
must_fail("div.mermaid in Artifact mode", swap('<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4.2.4/dist/index.global.js"></script>', "", CLEAN), 'use <pre class="mermaid">', artifact=True)

# ── must fire: language ────────────────────────────────────────────────────
must_fail("Thai body with lang=en", swap('<html lang="th">', '<html lang="en">', CLEAN), "wrong line-breaking rules")
must_fail("no lang at all", swap('<html lang="th">', "<html>", CLEAN), "needs a non-empty lang")
must_fail("overflow-wrap anywhere", swap("line-height: 1.6;", "line-height: 1.6; overflow-wrap: anywhere;", CLEAN), "chops Thai mid-syllable")
must_fail("break-all utility", swap('class="skeleton"', 'class="skeleton break-all"', CLEAN), "break-all")

# ── must fire: structure ───────────────────────────────────────────────────
must_fail("tabs out of order", swap('id="tab-flows"', 'id="tab-zz"', CLEAN).replace('id="tab-ia"', 'id="tab-flows"').replace('id="tab-zz"', 'id="tab-ia"'), "out of order")
must_fail("flows tab with no mermaid", swap('<div class="mermaid">sequenceDiagram; A->>B: ขอยืม</div>', "<div>กล่องกับลูกศรที่วาดเอง</div>", CLEAN), "no mermaid block")
must_fail("no registry", swap("const screens = {", "const notScreens = {", CLEAN), "could not find the `screens")

# ── must fire: the annotation contract ─────────────────────────────────────
must_fail("orphan callout", swap('style="top:-8px;right:-8px">2<', 'style="top:-8px;right:-8px">4<', CLEAN), "callout [4] in the frame has no line")
must_fail("orphan annotation", swap('<span class="wf-callout" style="top:-8px;right:-8px">2</span>', "", CLEAN), "annotation [2] has no callout")
must_fail("duplicate number", swap("{ n: 2, tag:", "{ n: 1, tag:", CLEAN), "duplicate annotation number")
must_fail("gap in numbering", swap("{ n: 2, tag:", "{ n: 3, tag:", swap('right:-8px">2<', 'right:-8px">3<', CLEAN)), "must run 1..2 with no gaps")
must_fail("unknown tag", swap('tag: "error"', 'tag: "note"', CLEAN), "unknown tag `note`")
must_fail("missing why", swap('why: "คิวทั้งสามอยู่หน้าเดียวเพราะเจ้าหน้าที่คนเดียวดูแลทั้งหมด (ADR 0001)",', "", CLEAN), "has no `why`")
must_fail("missing route", swap('route: "/app/borrow-requests",', "", CLEAN), "has no route")
must_fail("empty annotation text", swap('text: "สถานะแท็บเก็บใน URL — รีเฟรชแล้วอยู่แท็บเดิม"', 'text: ""', CLEAN), "empty text")


def main() -> int:
    passed = failed = 0
    for name, source, needle, flags in CASES:
        errors, warnings = run(source, **flags)
        if needle is None:
            ok = not errors
            detail = "; ".join(errors)
        else:
            ok = any(needle in message for message in errors)
            detail = "; ".join(errors) or "(no errors raised)"
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"FAIL {name}")
            print(f"     expected: {'silence' if needle is None else needle!r}")
            print(f"     got:      {detail}")
        if needle is None and warnings:
            print(f"     note {name}: warnings {warnings}")
    print(f"\n{passed} passed, {failed} failed  ({len(CASES)} cases)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
