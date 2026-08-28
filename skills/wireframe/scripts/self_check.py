#!/usr/bin/env python3
"""Self-check a generated wireframe HTML file. No third-party dependencies.

Ships inside the skill so an installed agent can verify its own output before
handing it over:

    python3 <skill-dir>/scripts/self_check.py docs/wireframes/my-app.html

It turns the rules SKILL.md states in prose into pass/fail: grayscale-only,
flat-only, callout/annotation pairing, the six annotation tags, no Lorem, no
unreplaced {{...}}, no external images, no dark mode, and the Thai typography
contract. Modes:

    --template   the file is references/template.html, not a deliverable:
                 {{...}} placeholders and dangling nav targets are expected
    --artifact   the file is built for Artifact mode (strict CSP): no remote
                 asset at all, and mermaid must be <pre>, not a module import
    --strict     treat warnings as failures

What it deliberately does NOT check, because a static reader cannot: whether a
route exists in the real code, whether the page scrolls horizontally at 375px,
whether a `why` cites a rule instead of describing the picture, and whether the
annotation says something the picture already says. Those stay human items on
the SKILL.md §3 checklist.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TAGS = {"behavior", "rule", "error", "a11y", "dev", "open"}
TAB_ORDER = ["overview", "ia", "flows", "screens", "review"]

# Tailwind color families that carry hue. The neutral ramps are left out on
# purpose — the skill ships its own gray tokens and those are what should be used.
CHROMATIC_FAMILIES = (
    "red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo"
    "|violet|purple|fuchsia|pink|rose"
)
COLOR_UTILITIES = "bg|text|border|ring|outline|decoration|divide|accent|caret|fill|stroke|from|via|to"

# Every CSS named color that is not achromatic. The achromatic ones — black,
# white, gray/grey, dark/light/dimgray, silver, gainsboro, whitesmoke — are legal.
CHROMATIC_NAMES = frozenset("""
aliceblue antiquewhite aqua aquamarine azure beige bisque blanchedalmond blue
blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue
cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgreen darkkhaki
darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon darkseagreen
darkslateblue darkslategray darkslategrey darkturquoise darkviolet deeppink
deepskyblue dodgerblue firebrick floralwhite forestgreen fuchsia ghostwhite gold
goldenrod green greenyellow honeydew hotpink indianred indigo ivory khaki
lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan
lightgoldenrodyellow lightgreen lightpink lightsalmon lightseagreen lightskyblue
lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen
magenta maroon mediumaquamarine mediumblue mediumorchid mediumpurple
mediumseagreen mediumslateblue mediumspringgreen mediumturquoise mediumvioletred
midnightblue mintcream mistyrose moccasin navajowhite navy oldlace olive
olivedrab orange orangered orchid palegoldenrod palegreen paleturquoise
palevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple
red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna
skyblue slateblue slategray slategrey snow springgreen steelblue tan teal thistle
tomato turquoise violet wheat yellow yellowgreen
""".split())

# The two remote scripts the non-Artifact template is allowed to load.
ALLOWED_HOSTS = ("cdn.jsdelivr.net",)

HEX_RE = re.compile(r"(?:#|%23)([0-9a-fA-F]{3,8})(?![0-9a-fA-F])")
FUNC_COLOR_RE = re.compile(r"\b(rgba?|hsla?)\(([^()]*)\)", re.I)
COLOR_DECL_RE = re.compile(
    r"\b(?:color|background|background-color|border(?:-[a-z]+)?|outline(?:-color)?"
    r"|fill|stroke|stop-color|flood-color|caret-color|accent-color|column-rule(?:-color)?"
    r"|text-decoration(?:-color)?)\s*:\s*([^;{}\n]{1,200})",
    re.I,
)
CLASS_ATTR_RE = re.compile(r'class\s*=\s*"([^"]*)"|class\s*=\s*\'([^\']*)\'')
TW_COLOR_RE = re.compile(
    rf"(?:^|[\s:])(?:{COLOR_UTILITIES})-(?:{CHROMATIC_FAMILIES})(?:-\d{{2,3}})?\b"
)


# ──────────────────────────── source preparation ────────────────────────────


def _blank(match: re.Match[str]) -> str:
    """Replace a span with spaces, keeping newlines so offsets and lines hold."""
    return "".join(c if c == "\n" else " " for c in match.group(0))


def strip_comments(source: str) -> str:
    """Blank HTML, CSS and JS comments without changing any offset.

    Rules written in a comment ("no box-shadow anywhere") must not be mistaken
    for the thing they forbid, and a hex value quoted in a comment is not a
    declaration. `/* */` and `//` are only stripped inside <style> and <script>,
    because a wireframe is full of route globs like `/app/*` and `/liff/*` that
    would otherwise open a comment and swallow the rest of the page.
    """

    def scrub(match: re.Match[str]) -> str:
        body = re.sub(r"/\*.*?\*/", _blank, match.group(2), flags=re.S)
        # `(?<![:\\])` keeps the `//` of https:// and of escaped paths intact.
        body = re.sub(r"(?<![:\\])//[^\n]*", _blank, body)
        return match.group(1) + body + match.group(3)

    source = re.sub(r"<!--.*?-->", _blank, source, flags=re.S)
    return re.sub(
        r"(<(?:style|script)\b[^>]*>)(.*?)(</(?:style|script)\s*>)",
        scrub,
        source,
        flags=re.S | re.I,
    )


def line_of(source: str, index: int) -> int:
    return source.count("\n", 0, index) + 1


def js_code_mask(body: str) -> bytearray:
    """1 where a character is JS code, 0 inside a string or template literal.

    Brace matching over a registry full of HTML template literals is only
    reliable if quoted text is excluded first.
    """
    n = len(body)
    mask = bytearray(b"\x01" * n)
    stack: list[list] = []  # ["str", quote] | ["tpl"] | ["sub", depth]
    i = 0
    while i < n:
        char = body[i]
        top = stack[-1][0] if stack else None
        if top == "str":
            mask[i] = 0
            if char == "\\":
                if i + 1 < n:
                    mask[i + 1] = 0
                i += 2
                continue
            if char == stack[-1][1]:
                stack.pop()
            i += 1
            continue
        if top == "tpl":
            mask[i] = 0
            if char == "\\":
                if i + 1 < n:
                    mask[i + 1] = 0
                i += 2
                continue
            if char == "`":
                stack.pop()
                i += 1
                continue
            if char == "$" and i + 1 < n and body[i + 1] == "{":
                mask[i + 1] = 0
                stack.append(["sub", 0])
                i += 2
                continue
            i += 1
            continue
        # code, either top level or inside a ${...} substitution
        if char in "\"'":
            mask[i] = 0
            stack.append(["str", char])
        elif char == "`":
            mask[i] = 0
            stack.append(["tpl"])
        elif top == "sub" and char == "{":
            stack[-1][1] += 1
        elif top == "sub" and char == "}":
            if stack[-1][1] == 0:
                mask[i] = 0
                stack.pop()
            else:
                stack[-1][1] -= 1
        i += 1
    return mask


def balanced(text: str, mask: bytearray, start: int, opener: str, closer: str) -> int:
    """Index just past the closer matching the opener at `start`, or -1."""
    depth = 0
    for i in range(start, len(text)):
        if not mask[i]:
            continue
        if text[i] == opener:
            depth += 1
        elif text[i] == closer:
            depth -= 1
            if depth == 0:
                return i + 1
    return -1


STRING_RE = re.compile(r'"((?:[^"\\]|\\.)*)"' r"|'((?:[^'\\]|\\.)*)'" r"|`((?:[^`\\]|\\.)*)`", re.S)


def field(entry: str, name: str) -> str | None:
    """The string value of `name:` in a JS object literal, unescaped enough."""
    match = re.search(rf"(?<![\w$]){re.escape(name)}\s*:\s*", entry)
    if not match:
        return None
    value = STRING_RE.match(entry, match.end())
    if not value:
        return None
    return next(group for group in value.groups() if group is not None)


# ─────────────────────────────── the checks ────────────────────────────────


class Report:
    def __init__(self, source: str) -> None:
        self.source = source
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str, index: int | None = None) -> None:
        self.errors.append(self._at(message, index))

    def warn(self, message: str, index: int | None = None) -> None:
        self.warnings.append(self._at(message, index))

    def _at(self, message: str, index: int | None) -> str:
        if index is None:
            return message
        return f"line {line_of(self.source, index)}: {message}"


def hex_is_gray(digits: str) -> bool | None:
    """True/False for an achromatic check, None when the length is not a color."""
    if len(digits) in (3, 4):
        red, green, blue = digits[0], digits[1], digits[2]
    elif len(digits) in (6, 8):
        red, green, blue = digits[0:2], digits[2:4], digits[4:6]
    else:
        return None
    return red.lower() == green.lower() == blue.lower()


def check_grayscale(doc: str, report: Report) -> None:
    """Principle 6: grayscale until hi-fi — no hue anywhere."""
    for match in HEX_RE.finditer(doc):
        gray = hex_is_gray(match.group(1))
        if gray is False:
            report.error(f"hue found: #{match.group(1)} is not gray", match.start())

    for match in FUNC_COLOR_RE.finditer(doc):
        name = match.group(1).lower()
        parts = [p.strip() for p in re.split(r"[,\s/]+", match.group(2).strip()) if p.strip()]
        if name.startswith("hsl"):
            if len(parts) >= 2 and not re.fullmatch(r"0(?:\.0+)?%?", parts[1]):
                report.error(
                    f"hue found: {match.group(0)} has non-zero saturation", match.start()
                )
        elif len(parts) >= 3 and len({p.rstrip("%") for p in parts[:3]}) > 1:
            report.error(f"hue found: {match.group(0)} channels differ", match.start())

    for match in COLOR_DECL_RE.finditer(doc):
        for word in re.findall(r"[A-Za-z]{3,}", match.group(1)):
            if word.lower() in CHROMATIC_NAMES:
                report.error(f"hue found: named color `{word}`", match.start())

    for match in CLASS_ATTR_RE.finditer(doc):
        classes = match.group(1) or match.group(2) or ""
        for hit in TW_COLOR_RE.finditer(classes):
            report.error(f"hue found: Tailwind class `{hit.group(0).strip()}`", match.start())


def check_flat(doc: str, report: Report) -> None:
    """Flat only — no shadow, no gradient. Depth is borders and flat fills."""
    for match in re.finditer(r"box-shadow\s*:\s*([^;{}\n]+)", doc, re.I):
        if match.group(1).strip().lower() not in ("none", "none;"):
            report.error(f"box-shadow is not allowed: {match.group(0).strip()}", match.start())
    for match in re.finditer(r"\b(?:linear|radial|conic|repeating-\w+)-gradient\s*\(", doc, re.I):
        report.error("gradient is not allowed", match.start())
    for match in CLASS_ATTR_RE.finditer(doc):
        classes = match.group(1) or match.group(2) or ""
        for hit in re.finditer(r"(?:^|[\s:])(shadow(?!-none)(?:-[\w[\]./]+)?)\b", classes):
            report.error(f"shadow utility is not allowed: `{hit.group(1)}`", match.start())
        for hit in re.finditer(r"(?:^|[\s:])(bg-gradient-to-\w+)\b", classes):
            report.error(f"gradient utility is not allowed: `{hit.group(1)}`", match.start())


def check_content(doc: str, report: Report, template_mode: bool) -> None:
    """Content hygiene the SKILL.md `Never` list spells out."""
    for match in re.finditer(r"lorem\s+ipsum|dolor\s+sit\s+amet", doc, re.I):
        report.error("Lorem ipsum is never allowed, at any fidelity", match.start())

    if not template_mode:
        placeholders = list(re.finditer(r"\{\{[^{}]{0,120}\}\}", doc))
        if placeholders:
            report.error(
                f"{len(placeholders)} unreplaced {{{{...}}}} placeholder(s) left, "
                f"first at line {line_of(doc, placeholders[0].start())}"
            )

    for pattern in (r"\bItem\s*1\b", r"รายการ\s*1\b"):
        sibling = pattern.replace("1", "2")
        if re.search(pattern, doc) and re.search(sibling, doc):
            report.warn("placeholder names like `Item 1 / Item 2` — use realistic sample data")

    for match in re.finditer(r"prefers-color-scheme\s*:\s*dark", doc, re.I):
        report.error("no dark mode inside a wireframe", match.start())
    for match in CLASS_ATTR_RE.finditer(doc):
        classes = match.group(1) or match.group(2) or ""
        if re.search(r"(?:^|\s)dark:", classes):
            report.error("no dark mode inside a wireframe: `dark:` variant", match.start())


def check_assets(doc: str, report: Report, artifact_mode: bool) -> None:
    """One self-contained file: no real images, no font request, no stray CDN."""
    if re.search(r"fonts\.(?:googleapis|gstatic)\.com", doc, re.I):
        report.error(
            "no Google Fonts link — it dies under the Artifact CSP and reflows every screen"
        )

    for match in re.finditer(r"""(?:src|href)\s*=\s*["'](https?:)?//([^"'/]+)""", doc, re.I):
        host = match.group(2)
        if artifact_mode:
            report.error(f"Artifact mode allows no remote asset: {host}", match.start())
        elif not host.endswith(ALLOWED_HOSTS):
            report.error(f"unexpected remote asset: {host}", match.start())

    for match in re.finditer(r"url\(\s*['\"]?(https?:)?//", doc, re.I):
        report.error("no external image — inline an SVG data URI instead", match.start())
    for match in re.finditer(r"<img\b[^>]*\bsrc\s*=\s*[\"'](?!data:)", doc, re.I):
        report.error("no real or external images in a wireframe", match.start())
    for match in re.finditer(r"@import\b", doc, re.I):
        report.error("no CSS @import", match.start())

    if artifact_mode:
        for match in re.finditer(r"<div\b[^>]*class\s*=\s*[\"'][^\"']*\bmermaid\b", doc, re.I):
            report.error(
                "Artifact mode renders mermaid natively: use <pre class=\"mermaid\">, not <div>",
                match.start(),
            )


def check_language(doc: str, report: Report) -> None:
    """The Thai typography contract in SKILL.md § Language & type."""
    match = re.search(r"<html\b[^>]*\blang\s*=\s*[\"']([^\"']*)[\"']", doc, re.I)
    if not match or not match.group(1).strip():
        report.error("<html> needs a non-empty lang — it drives line breaking")
        lang = ""
    else:
        lang = match.group(1).strip().lower()

    has_thai = any("฀" <= ch <= "๿" for ch in doc)
    if has_thai and not lang.startswith("th"):
        report.error(f"Thai content but lang=\"{lang}\" — wrong line-breaking rules")

    for bad in re.finditer(r"(?:word-break|overflow-wrap|line-break)\s*:\s*anywhere", doc, re.I):
        report.error(
            "`anywhere` chops Thai mid-syllable — use overflow-wrap: break-word", bad.start()
        )
    for bad in CLASS_ATTR_RE.finditer(doc):
        classes = bad.group(1) or bad.group(2) or ""
        if re.search(r"(?:^|\s)break-all\b", classes):
            report.error("`break-all` chops Thai mid-syllable — use break-words", bad.start())

    if has_thai:
        heights = [
            float(m.group(1))
            for m in re.finditer(r"line-height\s*:\s*(\d+(?:\.\d+)?)\s*(?:;|\})", doc)
        ]
        if not heights or max(heights) < 1.6:
            report.warn("Thai content wants line-height 1.6 or more on html/body")


def check_structure(doc: str, report: Report) -> None:
    """The five tabs, in order, and the rule that flows are real mermaid."""
    found = [m.group(1) for m in re.finditer(r'id\s*=\s*"tab-([a-z]+)"', doc)]
    tabs = [name for name in found if name in TAB_ORDER]
    expected = [name for name in TAB_ORDER if name in tabs]
    if tabs != expected:
        report.error(f"tab panels are out of order: {tabs} — keep the order {TAB_ORDER}")

    flows = re.search(r'id\s*=\s*"tab-flows"', doc)
    if flows:
        rest = doc[flows.end():]
        section = rest.split('id="tab-', 1)[0]
        if not re.search(r'class\s*=\s*"[^"]*\bmermaid\b', section):
            report.error(
                "the Flows tab has no mermaid block — flows are always real mermaid, "
                "never divs and arrows"
            )
    if "wf-callout" not in doc:
        report.warn("no .wf-callout anywhere — a wireframe without annotations is not a deliverable")


# ───────────────────────────── screen registry ─────────────────────────────


CALLOUT_RE = re.compile(r"wf-callout[^>]*>\s*([^<\s][^<]*?)\s*<")


def find_registry(source: str) -> tuple[str, int] | None:
    """The balanced body of `const screens = { ... }`, with its absolute offset."""
    for script in re.finditer(r"<script\b[^>]*>(.*?)</script>", source, re.S | re.I):
        body = script.group(1)
        opener = re.search(r"(?<![\w$])(?:const|let|var)?\s*screens\s*=\s*\{", body)
        if not opener:
            continue
        mask = js_code_mask(body)
        start = body.index("{", opener.start())
        end = balanced(body, mask, start, "{", "}")
        if end == -1:
            return None
        return body[start:end], script.start(1) + start
    return None


def split_entries(block: str) -> list[tuple[str, str, int]]:
    """Top-level `"id": { ... }` entries as (id, body, offset-in-block)."""
    mask = js_code_mask(block)
    entries: list[tuple[str, str, int]] = []
    depth = 0
    i = 0
    key: tuple[str, int] | None = None
    while i < len(block):
        if not mask[i]:
            # A quoted key sits inside a masked string; read it whole.
            if depth == 1 and block[i] in "\"'":
                match = STRING_RE.match(block, i)
                if match:
                    text = next(g for g in match.groups() if g is not None)
                    tail = block[match.end():]
                    if re.match(r"\s*:", tail):
                        key = (text, match.end())
                    i = match.end()
                    continue
            i += 1
            continue
        char = block[i]
        if char == "{":
            depth += 1
            if depth == 2 and key:
                end = balanced(block, mask, i, "{", "}")
                if end == -1:
                    break
                entries.append((key[0], block[i:end], i))
                key = None
                i = end
                depth -= 1
                continue
        elif char == "}":
            depth -= 1
        elif depth == 1 and (char.isalpha() or char in "_$"):
            match = re.match(r"[\w$-]+", block[i:])
            if match and re.match(r"\s*:", block[i + match.end():]):
                key = (match.group(0), i + match.end())
                i += match.end()
                continue
        i += 1
    return entries


def check_registry(source: str, report: Report, template_mode: bool) -> None:
    found = find_registry(source)
    if not found:
        report.error(
            "could not find the `screens = { ... }` registry — it drives navigation, "
            "deep links and the annotation panel"
        )
        return
    block, offset = found
    entries = split_entries(block)
    if not entries:
        report.error("the screens registry is empty")
        return

    known = {name for name, _, _ in entries}

    for name, body, at in entries:
        where = offset + at
        label = f"screen `{name}`"

        if not (field(body, "route") or "").strip():
            report.error(f"{label} has no route — a state is a screen, so it needs one", where)
        why = (field(body, "why") or "").strip()
        if not why:
            report.error(f"{label} has no `why` — the rule behind the layout", where)

        ann_start = re.search(r"(?<![\w$])annotations\s*:\s*\[", body)
        numbers: list[int] = []
        if ann_start:
            mask = js_code_mask(body)
            open_bracket = body.index("[", ann_start.start())
            end = balanced(body, mask, open_bracket, "[", "]")
            array = body[open_bracket:end] if end != -1 else ""
            html_part = body[:open_bracket] + body[end:] if end != -1 else body
            amask = js_code_mask(array)
            i = 0
            while i < len(array):
                if amask[i] and array[i] == "{":
                    stop = balanced(array, amask, i, "{", "}")
                    if stop == -1:
                        break
                    obj = array[i:stop]
                    raw_n = re.search(r"(?<![\w$])n\s*:\s*(\d+)", obj)
                    tag = field(obj, "tag")
                    text = (field(obj, "text") or "").strip()
                    if not raw_n:
                        report.error(f"{label}: an annotation has no `n`", where)
                    else:
                        numbers.append(int(raw_n.group(1)))
                    if tag is None:
                        report.error(f"{label}: an annotation has no `tag`", where)
                    elif tag not in TAGS:
                        report.error(
                            f"{label}: unknown tag `{tag}` — use one of "
                            f"{', '.join(sorted(TAGS))}",
                            where,
                        )
                    if not text:
                        report.error(f"{label}: an annotation has empty text", where)
                    i = stop
                    continue
                i += 1
        else:
            html_part = body

        marks: list[int] = []
        for hit in CALLOUT_RE.finditer(html_part):
            value = hit.group(1)
            if value.isdigit():
                marks.append(int(value))
            else:
                report.warn(
                    f"{label}: callout number `{value}` is computed — cannot be paired", where
                )

        if len(numbers) != len(set(numbers)):
            duplicates = sorted({n for n in numbers if numbers.count(n) > 1})
            report.error(f"{label}: duplicate annotation number(s) {duplicates}", where)
        if numbers and sorted(set(numbers)) != list(range(1, len(set(numbers)) + 1)):
            report.error(
                f"{label}: annotation numbers must run 1..{len(set(numbers))} with no gaps, "
                f"got {sorted(set(numbers))}",
                where,
            )

        orphan_marks = sorted(set(marks) - set(numbers))
        orphan_notes = sorted(set(numbers) - set(marks))
        if orphan_marks:
            report.error(
                f"{label}: callout {orphan_marks} in the frame has no line in the panel", where
            )
        if orphan_notes:
            report.error(
                f"{label}: annotation {orphan_notes} has no callout in the frame", where
            )
        if not numbers and not marks:
            report.warn(f"{label} has no annotations — the picture cannot carry it alone", where)

    if not template_mode:
        targets = set()
        for match in re.finditer(r'data-go\s*=\s*"([^"$]+)"', source):
            targets.add((match.group(1), match.start()))
        for match in re.finditer(r'(?<![\w$])id\s*:\s*"([^"$]+)"', source):
            targets.add((match.group(1), match.start()))
        for target, at in sorted(targets):
            if target not in known:
                report.warn(f"`{target}` is navigated to but is not a screen in the registry", at)


# ─────────────────────────────────── cli ───────────────────────────────────


def verify(path: Path, template_mode: bool, artifact_mode: bool) -> Report:
    raw = path.read_text(encoding="utf-8")
    doc = strip_comments(raw)
    report = Report(raw)
    check_grayscale(doc, report)
    check_flat(doc, report)
    check_content(doc, report, template_mode)
    check_assets(doc, report, artifact_mode)
    check_language(doc, report)
    check_structure(doc, report)
    check_registry(doc, report, template_mode)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--template", action="store_true", help="the file is the shipped template")
    parser.add_argument("--artifact", action="store_true", help="built for Artifact mode (strict CSP)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args(argv)

    failed = False
    for path in args.files:
        try:
            report = verify(path, args.template, args.artifact)
        except (OSError, UnicodeError) as exc:
            print(f"FAIL {path}\n  - {exc}")
            failed = True
            continue
        bad = report.errors or (args.strict and report.warnings)
        print(f"{'FAIL' if bad else 'OK'} {path}")
        for message in report.errors:
            print(f"  - {message}")
        for message in report.warnings:
            print(f"  ~ {message}")
        failed = failed or bool(bad)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
