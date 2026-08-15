---
name: wireframe
description: Build an interactive annotated wireframe as a single self-contained HTML file — screen map / IA, user flows (mermaid), device-framed screens with numbered callouts and an annotation panel, plus review questions. Use whenever the user asks to design, draw, annotate, or review wireframes, screen structure, sitemap, IA, user flow, mockup, prototype, "โครงหน้าจอ", "แผนผังหน้า", "wireframe", "mockup", "flow", or wants to see all screens of an app before coding.
---

# Wireframe — annotated, single HTML file

Deliverable is one `.html` file that opens in a browser with no build step. Tabs: Overview → Screen map → Flows → Screens → Review.

- `references/template.html` — ready-to-copy scaffold; replace every `{{...}}`
- `references/conventions.md` — standard wireframe conventions; read it when deciding fidelity or what to annotate. **This file wins any conflict with it.**

**A wireframe without annotations is not a deliverable** — it is a set of gray boxes everyone interprets differently. The picture shows *what it looks like*; annotations explain *how it behaves and why*.

## Language & type

Write **UI labels, screen names, sample data, the page chrome (tab names, panel headings, legend), and the annotation text** in the language the real app uses. Only these stay English, because they are structural keys the tooling matches on: the six **annotation tags** (`behavior` / `rule` / …), screen **ids**, and **routes**.

For a Thai app:

- `<html lang="th">` — wrong `lang` gives the browser the wrong line-breaking rules
- **One font stack, no webfont** — `system-ui, -apple-system, "Noto Sans Thai", sans-serif`, identical in normal and Artifact mode. Never a Google Fonts link: it dies under the Artifact CSP and silently reflows every screen you already checked
- `line-height: 1.6` minimum — Thai ascenders and tone marks need more leading than Latin at the same size
- **`overflow-wrap: break-word`, never `anywhere`** — Thai has no spaces, so `anywhere` chops words mid-syllable
- Dates: pick พ.ศ. or ค.ศ. per the real app and use it in *every* sample value — mixed eras in sample data read as a bug
- Thai labels run ~15–20% longer than the English draft. Size buttons and table columns for the Thai string, not the English one

## Screen widths

Three numbers, and they are not interchangeable:

| width | what it is |
|---|---|
| **360px** | inside the `phone()` frame — the narrowest real device the app must survive |
| **375px** | the width the *wireframe document* is checked at; 360 + border fits inside it, which is why the page must never scroll horizontally there |
| **900px** | where the *wireframe document* collapses desktop frames to one column — a property of this page, **not** a breakpoint of the app being designed |

Draw a screen at **both `phone()` and `desktop()`** when the two layouts differ in more than width — different navigation, a column that disappears, an action bar that moves. One frame is enough when the desktop version is the same structure stretched. If the product's own breakpoints matter, they are an annotation (`dev`), never inferred from the 900px above.

---

## Principles (non-negotiable)

1. **Ground truth before drawing** — routes, menu names, field names, roles are copied from real code or docs, never invented. If no code exists yet, work from the spec and state the source in the page header.
2. **Hierarchy must survive without color** — establish it through size, position, and grouping. If the screen still reads correctly in pure grayscale, the structure is right.
3. **The rougher the wireframe, the more it needs annotation** — lo-fi needs more notes than hi-fi, because the picture carries less.
4. **A state is a screen, not a footnote** — empty / loading / error / success / dialog / toast / printed document each get their own entry, with a route like `/liff/requisition-new · empty`.
5. **Annotate while drawing, not after** — the reasoning is lost if you wait.
6. **Grayscale until hi-fi — no hue anywhere** — not in the chrome, not in the frames, and not for status. A wireframe wearing brand colors gets read as finished visual design, and reviewers start arguing about shades instead of structure. Emphasis comes from fill darkness, weight, border, and grouping. Pull the project's real tokens from `src/index.css` / `tailwind.config.*` / `design-system.ts` only when moving to hi-fi.

---

## Annotation system

The core of the deliverable. Always **numbered callouts ↔ a numbered panel**. Never draw arrows to labels — they clutter the frame.

```js
"app-inbox": {
  group: "App", label: "Pending queue", route: "/app/borrow-requests",
  why: "All three queues live on one screen because one officer owns all three",  // screen-level rationale
  annotations: [
    { n: 1, tag: "behavior", text: "Tab state is kept in the URL — refresh lands on the same tab" },
    { n: 2, tag: "rule",     text: "Whole-request approval only; per-item buttons are omitted deliberately (ADR 0001)" },
    { n: 3, tag: "error",    text: "If an item gets borrowed while pending → red toast, the whole request fails" },
    { n: 4, tag: "open",     text: "Undecided: how the member is notified after a rejection" },
  ],
  html: () => desktop(...),  // place <span class="wf-callout">1</span> at the matching spot
}
```

### Tags

| tag | use for | example |
|---|---|---|
| `behavior` | what happens on tap / scroll / wait | "Expands details inline; does not open a new page" |
| `rule` | business rule that dictates the layout; cite the ADR/spec | "Module off → hide nav + block route + API 403" |
| `error` | error, validation, failure branches | "Blurry photo over threshold → upload blocked, retake required" |
| `a11y` | focus order, labels, touch target size | "Bottom action bar is 48px tall — reachable one-handed by thumb" |
| `dev` | what an implementer must know but cannot see | "Table virtualizes past 200 rows" |
| `open` | undecided points that need an answer | "Unclear who may cancel after approval" |

### What to annotate / what not to

**Must have** — interactive elements and hidden states · anything implemented differently than a reader would assume · the destination of every CTA · error handling · business rules that force the layout · decisions still open.

**Never include** — things already visible ("this is the menu bar") · pixel values and colors that belong in the design system · paragraph-length explanations.

**Write the fewest words that still carry the point, and give the reason rather than the name.**

- ✗ "This is a hidden menu bar"
- ✓ "Menu is collapsed to cut clutter on mobile; the top-right icon opens it"

### Numbering

Numbers run **per screen**, restarting at 1 on every screen — editing one screen then never renumbers the others. Position with `style="top:-8px;right:-8px"` on a `relative` parent, ordered the way the eye reads the screen (top-left to bottom-right).

---

## Fidelity

Default is **mid-fi**. Ask if unclear.

| | lo-fi | **mid-fi** | hi-fi |
|---|---|---|---|
| use when | structure still uncertain, want fast feedback | structure settled, filling in detail | close to implementation / user testing |
| color | grayscale | grayscale — still no hue, only more steps of it | full design system, project tokens swapped in |
| content | `.wf-line` for text, `.wf-img` for images | real or near-real copy at realistic length | final copy |
| annotation | **heaviest** | moderate | lightest — the picture speaks |
| data | none | realistic samples (`EQ-00412`, `001/2569`) | real data |

**Never use Lorem ipsum at any fidelity** — fake text length leads to wrong layout decisions. With no copy yet, use `.wf-line` at a realistic width instead.

---

## Process

### 0. Recon — gather ground truth before writing a line

You need: **every route · menu labels verbatim · design tokens · roles and permissions · business rules that constrain the UI.** Where those live depends on the stack — find them, don't assume a React SPA:

| stack | routes | menu labels |
|---|---|---|
| React SPA | `rg -n "path:\|<Route\|createBrowserRouter" src/main.tsx src/App.tsx src/router*` | `rg -n "title\|label\|href\|icon" src/components/*sidebar* src/components/*nav*` |
| Next.js App Router | `fd -t d -g "**" app \| rg "page\.\|route\."` — the folder tree *is* the routes | `rg -n "label\|title" app/**/nav* components/**/nav*` |
| Remix / React Router v7 | `rg -n "route\(" app/routes.ts` or `ls app/routes/` | same as React SPA |
| WordPress | `rg -n "register_post_type\|add_rewrite_rule\|add_menu_page" --glob "*.php"` · template hierarchy in the theme | `rg -n "wp_nav_menu\|register_nav_menus" --glob "*.php"` |

```bash
rg -n "@theme|--color-|--font-" src/index.css app/globals.css tailwind.config.* src/lib/design-system.ts 2>/dev/null
ls docs/ docs/adr/ 2>/dev/null
```

**If the recon comes back empty, say so and stop — do not fill the gap by guessing.** Ask the owner where routes and labels live, or mark every screen `source: proposal` in the header.

### 1. Draft the screen inventory first

A `group / label / route / state / fidelity` table before any markup. Confirm it briefly with the user. Past ~20 screens, ask which surface to cover first. Group by **actor + surface** (`Member · LIFF`, `Officer · App`, `Documents`), not by route order.

### 2. Build from `references/template.html`

Replace tokens, product name, `APP_NAV`, `screens`, and the mermaid diagrams. **Write each screen's `annotations` at the same time as its `html`.**

### 3. Verify before delivering

- [ ] Every route exists in the code, or is explicitly marked as a proposal
- [ ] Every callout in a frame has a panel line, and every panel line has a callout — no orphans either direction
- [ ] No annotation restates something already visible
- [ ] Every screen has a `why` that cites a rule rather than describing the picture
- [ ] Every CTA has a destination (`data-go`, or an annotation naming it)
- [ ] Flows include failure branches (`alt` / `else`), not just the happy path
- [ ] Key states have their own screens — at minimum empty + error for the main feature
- [ ] Deep link `#screen=<id>` works · no horizontal page scroll at 375px
- [ ] Legend present · no Lorem ipsum · no dark mode · no real photography

### 4. Deliver

**Where the file goes depends on whether the project has a repo yet** — a wireframe is a spec, and a spec belongs next to the code it specifies:

| | path | why |
|---|---|---|
| project **has a dev repo** | `<repo>/docs/wireframes/<kebab-name>.html` | in git → diffable, tied to the PR that changed the screen, found by whoever implements it |
| project has **no repo yet** (pitch, IA exploration) | the knowledge base's own attachments dir, e.g. `assets/wireframes/<slug>-YYYY-MM-DD.html` | nowhere else to live yet — move it into `docs/wireframes/` the day the repo exists |

Never keep a second copy in a wiki or notes vault once the repo copy exists — link to the repo URL instead. Tell the user the path either way.

- **Publish as an Artifact** — load the `artifact-design` skill first, then apply Artifact mode below

---

## File structure

| Tab | answers | contains |
|---|---|---|
| **Overview** | how many surfaces, who sees what | surface cards, role → can do / blocked table, toggleable modules |
| **Screen map** | where each user type enters | mermaid `flowchart` per surface + menu IA |
| **Flows** | what the system revolves around | 3–5 `sequenceDiagram` / `flowchart`, each with its failure branch |
| **Screens** | how it looks and behaves | legend + left nav + stage + **annotation panel** |
| **Review** | what to detail next | 2–3 forms letting the user steer the next round |

**Flows are always real `.mermaid` blocks — never boxes and arrows hand-built from divs.** Mermaid lays itself out, stays diffable in git, and survives edits; a flowchart built from flexbox has to be redrawn by hand every time a branch changes.

## Toolkit inside the file

**Frames** — `desktop(activeNavId, breadcrumb, body)` (216px sidebar + topbar) · `phone(body)` (360×700) · `auth(body)` (two columns)

**Mobile grammar** — most native screens are just these: `navbar(title)` · `group(title, rows)` white block separated by the gray page gutter · `row(label, value, {chevron, disabled})` · `banner(title, sub)` for a rule governing the whole screen · `segmented(options, activeIndex)` · `toggle(on)` · `iconBox(glyph, label)` · `actionBar(secondary, primary)` pinned at the bottom · `metric(title, value, flag)` where `flag` is a word, never a severity color

**Placeholders** — `.wf-img` crossed box = image/logo (the standard convention) · `.wf-line` gray bar = text, width set realistically · `.skeleton` = content not yet decided · dashed border = disabled module or undesigned area

**Signals** — status, severity and urgency are written as **words**: a bordered chip reading `NEEDS ACTION`, heavier weight, a darker fill. Never a colored one. A red card sends reviewers to argue about the shade instead of the metric, and quietly promises a color decision the design system has not made yet.

**Palette** — nine steps of gray, no hue: `ink #1F1F1F` · `body #333` · `soft #6E6E6E` · `muted #9A9A9A` (disabled) · `line #DDD` · `line-strong #BFBFBF` · `fill #9B9B9B` (selected) · `surface #F4F4F4` · `bg #E8E8E8` (page and the gutter between sections). Selected state = `bg-fill` with white text. Primary button = `bg-ink` with white text. Secondary = white with a `line-strong` border.

**Flat only** — no `box-shadow` and no gradient anywhere. Separate surfaces with borders and flat fills. Elevation implies a lighting model the wireframe hasn't earned, and soft shadows are the fastest way to make a draft read as a finished screen. Where a shape genuinely needs drawing (the crossed image box, the graph grid), use an inline SVG data URI, not stacked gradients.

**Navigation** — any element with `data-go="<screen-id>"` switches screens via event delegation · `#screen=<id>` deep links

## Artifact mode (strict CSP)

Publishing through the Artifact tool blocks every off-host request, so change three things:

1. Drop CDN Tailwind → hand-write the CSS
2. Drop the mermaid ESM import → switch `<div class="mermaid">` to `<pre class="mermaid">` (artifacts render it natively)
3. Define the full palette on bare `:root` and set an explicit `background` on `body`

The font needs no change — the template already ships a webfont-free stack that is identical in both modes.

## Never

Guess a route without flagging it · Lorem ipsum · placeholder names like "Item 1 / Item 2" · real or external images · dark mode inside a wireframe · real interaction logic (validation, state machines) — a wireframe is structure, not a working prototype.
