# Industry conventions + sources

Distilled from published guidance. Use it when deciding fidelity, what to annotate, or how much detail is enough.

## Standard symbols

Widely shared across tools — readers who have seen a wireframe before recognize them without a legend (include one anyway).

| Symbol | Means |
|---|---|
| Box with a diagonal cross | Image or logo (a short label inside is fine) |
| Horizontal gray bars of varying length | Text — length signals heading vs. paragraph |
| Circle | Icon or avatar |
| Dashed border | Undesigned area, or a module that is switched off |
| Flat gray | Structure whose appearance is not decided yet |

**"Greeking"** — using fake text as a stand-in. Accepted practice, but Lorem ipsum misrepresents real length; gray bars or draft copy give truer layout decisions.

## Fidelity

- **lo-fi** optimizes learning speed when uncertainty is high — grayscale, coarse shapes, several variants side by side. Good for moderated usability tests of flow and navigation.
- **mid-fi** is where most teams spend most of their time — the lo-fi skeleton plus draft copy, brand accents starting to appear, explicit input types (radio / checkbox / dropdown), charts fed with real data, still not pixel-perfect.
- **hi-fi** optimizes execution clarity once uncertainty is low — demos and full usability testing.

The question is not "rough or detailed" but "what do we still not know" — more unknowns, rougher wireframe.

## Annotation

**The counterintuitive rule: the rougher the wireframe, the more annotation it needs.** A hi-fi mockup that speaks for itself needs fewer notes.

**Annotate** — elements with interaction or hidden state · anything implemented differently than a reader would assume · what happens as the user moves through a flow · error handling and validation · the outcome of every CTA · specific accessibility requirements (not generic statements).

**Format** — number them 1, 2, 3 and keep all text in a single column. Avoid arrows pointing into the frame; they clutter it. Use a color that contrasts clearly with the wireframe itself.

**Writing** — the fewest words that carry the point · framed from the user's perspective, not purely technical · include the reasoning behind the choice · written during wireframing, not after.

**Categories the field distinguishes** — behavior on interaction / design rationale / user-facing benefit / implementation notes for developers / copy specifications / pending decisions.

**Different readers want different things** — developers need exact behavior and the purpose of each element; designers want the user's-eye description. When only one layer fits, lean toward the developer, since wireframes are commonly used as handoff documentation.

## Layout principles

- Start from research and business goals, not from appearance
- **Hierarchy comes from size, position, and spatial grouping — not from color or typography.** Test by viewing in grayscale: if the most important element still stands out, the structure holds
- Use realistic content wherever possible
- Keep spacing and alignment consistent
- Pick the right starting screen size (mobile-first when the real users are on mobile)
- Reuse components instead of redrawing every screen
