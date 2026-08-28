<h1 align="center">wireframe-skill</h1>

<h3 align="center">Wireframes your reviewers can argue with — not admire.</h3>

An agent skill that turns a codebase into an **annotated grayscale wireframe**: one self-contained HTML file with a screen map, user flows, device-framed screens, and numbered notes explaining what the picture cannot.

The screens are mapped from real routes and real menu labels in the repo — not invented — so a review argues about the product instead of about a mock.

## Install

```sh
npx skills add kanwhile/wireframe-skill --skill wireframe
```

Add `-g` to install for all projects. Then ask for a wireframe in your own words, or invoke it directly in agents that expose skills as slash commands:

```
/wireframe map the whole admin surface before we build it
```

## What comes out

A single `.html` file that opens in a browser with no build step, in five tabs:

| Tab | Answers |
|---|---|
| **Overview** | How many surfaces, who sees what, what can be switched off |
| **Screen map** | Where each user type enters, and what sits under which module |
| **Flows** | What the system revolves around — including the branches that fail |
| **Screens** | Device-framed screens with numbered callouts and an annotation panel |
| **Review** | Questions that let the reviewer steer the next round |

## The rules it enforces

**Ground truth before drawing.** Routes, menu labels, field names, and roles are copied verbatim from the code. A wireframe that guesses names sends everyone arguing over something that does not exist.

**Grayscale until hi-fi — no hue anywhere.** Not in the chrome, not in the frames, not for status. Color is a promise the design system has not made yet; the moment it appears, reviewers start debating shades instead of structure. Emphasis comes from fill darkness, weight, border, and grouping.

**Flat only.** No shadows, no gradients. Elevation implies a lighting model the wireframe has not earned, and soft shadows are the fastest way to make a draft read as a finished screen.

**A state is a screen, not a footnote.** Empty, loading, error, success, dialog, toast, printed document — each gets its own entry with its own route, like `/checkout · empty`. A state with no picture is a state nobody builds.

**The rougher the wireframe, the more it needs annotation.** The counterintuitive one. A lo-fi sketch carries less on its own, so it needs more words — not fewer.

**Status is a word, not a color.** A chip reading `NEEDS ACTION`, not a red card. Red sends reviewers to argue about the shade instead of the number.

## Annotations

Numbered callouts paired with a numbered panel — never arrows dragged across the frame. Numbers restart at 1 on every screen, so editing one screen never renumbers the rest.

Each screen carries a `why` (the rule or ADR behind the layout, not a description of the picture) plus tagged notes:

| tag | for |
|---|---|
| `behavior` | what happens on tap, scroll, wait |
| `rule` | the business rule that dictates the layout |
| `error` | validation and failure branches |
| `a11y` | focus order, labels, touch targets |
| `dev` | what an implementer must know but cannot see |
| `open` | **decisions still unmade** |

`open` is the one that earns its keep. Every wireframe uncovers questions the code does not answer; this makes them visible instead of letting them evaporate.

## What's in the box

```
skills/wireframe/
├── SKILL.md                      the method: principles, process, checklist
├── references/
│   ├── template.html             ready-to-copy scaffold — replace every {{...}}
│   └── conventions.md            standard wireframe conventions and fidelity levels
└── scripts/
    └── self_check.py             fails the file on any rule a reader would miss
```

The template ships the frames (`desktop`, `phone`, `auth`), the mobile row/section grammar most native screens are built from (`navbar`, `group`, `row`, `banner`, `segmented`, `toggle`, `iconBox`, `actionBar`), the placeholder vocabulary (crossed box for an image, gray bars for text), and the screen registry that drives navigation, deep links, and the annotation panel.

## The checker

A rule that only lives in prose is a rule that ships broken. Before delivering, the skill runs its own output through a linter that ships with it — no dependencies, no build:

```sh
python3 skills/wireframe/scripts/self_check.py docs/wireframes/my-app.html
```

```
FAIL docs/wireframes/my-app.html
  - line 88: hue found: #eb6c36 is not gray
  - line 91: box-shadow is not allowed: box-shadow: 0 2px 8px #0000001a
  - line 240: screen `app-inbox`: callout [4] in the frame has no line in the panel
  - line 240: screen `app-inbox`: annotation [3] has no callout in the frame
  - line 302: screen `liff-form`: unknown tag `note`
```

It catches hue in every form it can hide in — hex, `rgb()`/`hsl()`, CSS named colors, Tailwind color utilities, even a color inside an SVG data URI — plus shadows, gradients, Lorem, unreplaced `{{...}}`, a Google Fonts link, external images, dark mode, `word-break: anywhere` against Thai, a Flows tab with no mermaid, and every way callouts and annotations can drift apart. `--artifact` tightens it for a strict-CSP build; `--strict` turns warnings into failures.

What it cannot see stays a human checklist item: whether a route exists in the real code, whether a `why` cites a rule or just describes the picture, whether an annotation says something the picture already said.

`scripts/test-self-check.py` keeps it honest with 48 adversarial cases — 36 mutations that must be caught and 12 legal shapes that must stay silent, because a checker that fires on everything gets switched off as fast as one that never fires.

## Notes

- UI labels and sample data follow the language of the app being wireframed. The skill itself is in English; a Thai product gets Thai screens.
- Flows are always real mermaid blocks — never boxes and arrows hand-built from divs.
- Never Lorem ipsum, at any fidelity. Fake text length leads to real layout mistakes.

## License

MIT
