# Dashboard: UX research and design brief

This document is the brief the dashboard is built from. It fixes who the
dashboard is for, what they need to do, how the screens are organised, and what
it should look like. Frontend workstreams (WS-4, WS-6–8) follow it; deviations
are proposed in the PR that makes them.

## 1. Who it is for

Two users are named in the assignment. Their needs pull in different directions,
and the design has to serve both on the same screen.

**Bob — drug developer running the trial.** Wants answers: what is in the data,
does his drug move any population, is there anything that predicts response. He
reads charts before tables and finding statements before methods. He will use
filters to poke at subsets. He is not a statistician and should never have to
compute anything himself.

**Yah — Bob's colleague, the sceptic.** Will not accept a claim without n, the
test, the p-value, the effect size, and whether multiple comparisons were handled.
She reads tables before charts and checks the cohort definition first. If the
dashboard hides a caveat, she finds it and the whole analysis loses credibility.

A third, implicit user: **the reviewer** opening the public link cold. Needs to
understand within a minute what the tool is, what the data is, and where the
answers to Parts 2–4 are.

## 2. What they need to do

| Task | Who | Success looks like |
| ---- | --- | ------------------ |
| Understand the dataset's shape | all | Projects, subjects, samples, conditions × treatments × sample types, time points visible without scrolling on the home page. |
| See the frequency of each population in each sample (Part 2) | Bob | Filter to any subset; sort by any column; see composition as a bar and a number; export the filtered table. |
| Compare responders and non-responders (Part 3) | Bob, Yah | The cohort definition is unmissable; five box plots with the raw points; a table with n, medians, IQR, U, p, q, effect size; a finding written from those numbers; per-subject and per-time-point views one click away. |
| Verify the statistics (Part 3) | Yah | The method, the adjustment, and the unit of analysis are stated on the same page; nothing has to be inferred. |
| Inspect the baseline miraclib cohort (Part 4) | Bob | The exact counts by project, response, and sex, with sample/subject clearly distinguished, and the list of samples. |
| Trust the numbers | reviewer, Yah | Provenance: input checksum, row counts, when it was generated, what library computed the test. |

## 3. Design principles

1. **Cohort first.** Every analytic view opens with the exact definition of the
   data it uses, as a narrowing sequence with counts at each step. This is the
   dashboard's signature element (see §5) and it answers Yah's first question
   before she asks it.
2. **Number and picture together.** No chart without its numbers, no table
   without the shape. Box plots show the points; tables show medians and IQR.
3. **Findings are generated, not typed.** The plain-language conclusion is
   rendered from the statistics with a fixed template, so it can never disagree
   with the table.
4. **Caveats are content.** Multiple-comparison adjustment, the repeated-measures
   issue, and the baseline-vs-on-treatment distinction appear inline where the
   claim is made, not in a footnote.
5. **Quiet chrome.** The data carries the visual weight. Navigation, filters, and
   panels are low-contrast and consistent; colour is reserved for meaning.

## 4. Information architecture

```
/            Overview        what the dataset is; entry points to the three questions
/samples     Samples         Part 2: per-sample composition, filterable, sortable, exportable
/response    Response        Part 3: responders vs non-responders, statistics, views
/baseline    Baseline cohort Part 4: the day-0 miraclib melanoma PBMC cohort; form-question aside
/methods     Methods         schema, tests, adjustment, provenance
```

Top navigation lists the five routes in that order with a one-line description on
hover. The route order follows the assignment so a reviewer can walk it top to
bottom.

### Global filter model

The filter bar on `/samples` filters the sample table on: project, condition,
treatment, sample type, time point, response, sex, plus a free-text match on
sample/subject id. Filters are AND across fields, OR within a field. State lives
in the URL query string so a filtered view can be shared. `/response` and
`/baseline` use fixed cohorts by definition and show their filters as read-only
cohort strips; a "open these samples in Samples" link carries the cohort into
the filterable view.

## 5. Screens

### Overview `/`

```
┌────────────────────────────────────────────────────────────────────────┐
│ Immune Atlas      Overview  Samples  Response  Baseline  Methods       │
├────────────────────────────────────────────────────────────────────────┤
│ Immune cell populations across a clinical trial dataset                │
│ 10,500 samples · 3,500 subjects · 3 projects · 5 populations · 3 time  │
│ points. Loaded from cell-count.csv (sha 0113…) on <date>.              │
│                                                                        │
│ Study structure                                                        │
│ ┌ condition × treatment ──────────────┐ ┌ sample type × time ────────┐ │
│ │ melanoma   miraclib  885 subj       │ │ PBMC  2,500 subj ×3 tp     │ │
│ │            phauximab 840            │ │ WB    1,000 subj ×3 tp     │ │
│ │ carcinoma  miraclib  680 …          │ └────────────────────────────┘ │
│ └─────────────────────────────────────┘                                │
│                                                                        │
│ Three questions                                                        │
│ ▸ What is the frequency of each population in each sample?  → Samples  │
│ ▸ Do responders differ from non-responders on miraclib?     → Response │
│ ▸ Who is in the baseline miraclib cohort?                   → Baseline │
└────────────────────────────────────────────────────────────────────────┘
```

The "three questions" block is a list of the assignment's questions in Bob's
words, each linking to its page. No KPI tiles.

### Samples `/samples`

```
┌ Filters: project ▾ condition ▾ treatment ▾ type ▾ time ▾ response ▾ sex ▾ [id…] │ Clear │ Download CSV ┐
│ 1,968 of 10,500 samples match                                                                 │
├──────────┬─────────┬──────────┬───────────┬──────┬────────────────────────────┬───────────────┤
│ sample   │ subject │ cond.    │ treatment │ time │ composition                │ total_count   │
│ s00000   │ sbj000  │ melanoma │ miraclib  │ 0    │ ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ │ 93,214        │
│  ↳ b_cell 11.70%  cd8 26.22%  cd4 21.98%  nk 14.87%  mono 25.22%   (expand row for the long form) │
```

Default view is wide (one row per sample with a stacked composition bar).
"Long table" toggle switches to the exact Part 2 layout (`sample, total_count,
population, count, percentage`), which is what the CSV download produces.
Paginated rows (100 per page) with a full pagination control; sticky header;
numbers right-aligned in tabular figures.

### Response `/response`

```
┌ Cohort ────────────────────────────────────────────────────────────────┐
│ All samples 10,500 ▸ melanoma 5,175 ▸ miraclib 2,655 ▸ PBMC 1,968      │
│ responders 993 samples / 331 subjects   non-responders 975 / 325        │
└────────────────────────────────────────────────────────────────────────┘
 Unit: (● per sample) (○ per subject)      Time point: (● all) (0) (7) (14)

 ┌ b_cell ────┐ ┌ cd8_t_cell ┐ ┌ cd4_t_cell ┐ ┌ nk_cell ───┐ ┌ monocyte ──┐
 │  ╷  ╷      │ │            │ │      ╷  ╷  │ │            │ │            │
 │ ┌┴┐┌┴┐     │ │  ...       │ │     ┌┴┐┌┴┐ │ │  ...       │ │  ...       │
 │ └┬┘└┬┘     │ │            │ │     └┬┘└┬┘ │ │            │ │            │
 │ yes  no    │ │            │ │  p 0.013 q 0.067 │        │ │            │
 └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘

 Finding
 Across 1,968 PBMC samples from 656 melanoma patients on miraclib, cd4_t_cell
 is the only population whose relative frequency differs between responders
 and non-responders at p < 0.05 (Mann–Whitney U, p = 0.013); after
 Benjamini–Hochberg adjustment across five populations it does not reach
 q < 0.05 (q = 0.067). Stratified by time point, no population differs at
 baseline; cd4_t_cell separates at day 7 and b_cell at day 14.

 ┌ population │ n yes │ n no │ median yes │ median no │ IQR … │ U │ p │ q │ effect │ Welch p ┐
```

The box plots are small multiples in one row on desktop, two rows on narrow
screens. Each plot draws the box, whiskers (1.5 IQR), median line, and every
sample as a jittered point at low opacity. Hovering a point shows sample id,
subject, time point, and percentage. Significance is shown as the numbers `p`
and `q` under each plot, not as stars.

### Baseline cohort `/baseline`

Cohort strip (melanoma ▸ miraclib ▸ PBMC ▸ day 0 ▸ 656 samples / 656 subjects),
then three compact horizontal bar charts with the exact counts printed at the
bar ends (by project: samples; by response: subjects; by sex: subjects), each
titled with its unit. Below, the sample list with subject metadata and a
download. A separate aside, visually set apart and labelled with its own filter,
shows the form question and its answer (485 samples, mean B cells 10,206.15) so
nobody mistakes it for the Part 4 cohort.

### Methods `/methods`

Sections: Data model (the schema as a diagram with a sentence per table),
Frequencies (the formula), Response comparison (test, effect size, adjustment,
unit of analysis, why — from ADR-0002), Provenance (run report table), Source
(links to `schema.sql`, `analysis/response.py`, the README).

## 6. Visual direction

The subject is immunology data from a clinical trial. Flow cytometry has a
visual vernacular — dot plots, gates, small multiples, monochrome density — and
clinical reporting has another — tables with n, precise typography, restrained
colour. The dashboard borrows from both and from nothing else.

**Signature element: the cohort strip.** A horizontal sequence of steps, each a
label and a count, joined by narrowing connectors so the eye reads the funnel:
`All samples 10,500 ▸ melanoma 5,175 ▸ miraclib 2,655 ▸ PBMC 1,968`. It is the
gating strategy of the analysis. It appears on every analytic page in the same
position and is the one place with a display-size number.

**Colour**

| Token | Value | Use |
| ----- | ----- | --- |
| `--paper` | `#F4F7FA` | page background (cool, not cream) |
| `--panel` | `#FFFFFF` | table and chart surfaces |
| `--ink` | `#14213D` | text, axes |
| `--ink-muted` | `#5B6B84` | secondary text, gridlines at 20% |
| `--rule` | `#DDE5EE` | borders and dividers |
| `--responder` | `#0891B2` | responders (teal; validated for chroma, CVD separation, and contrast) |
| `--non-responder` | `#B45309` | non-responders (ochre) |
| `--population-1…5` | `#1E3A8A` `#2F55B3` `#4F7BD9` `#86A8EA` `#BFD3F3` | the five populations in composition bars, ordered by `sort_order` |
| `--focus` | `#1D4ED8` | focus ring |

Teal/ochre is distinguishable under the common colour-vision deficiencies and
is used *only* for the responder/non-responder pair. Populations use a single-hue
ramp because they are read as a composition, not as five unrelated categories;
labels, not hue, identify them. There are no gradients, no shadows, and no
colour used decoratively.

**Typography**

- UI and body: IBM Plex Sans, 15 px base, `font-feature-settings: "tnum"` on
  every numeric cell.
- Page titles and the finding paragraph: IBM Plex Serif, 28 px / 18 px. The
  finding is set in serif to read as a written statement, distinct from the UI.
- Sample and subject identifiers in tables: IBM Plex Mono at 13 px, only there.
- Scale: 13 / 15 / 18 / 22 / 28 / 40 (cohort strip counts). Line length ≤ 75
  characters for prose.

**Layout**

- Left-aligned, max content width 1200 px, 24 px gutters, 8 px spacing grid.
- Top bar: wordmark left, five routes right, 56 px tall, `--paper` background
  with a `--rule` bottom border. No sidebar.
- Content blocks — tables, charts, the filter bar, the cohort strip, the
  question links — sit on `--panel` cards with a 1 px `--rule` border, 12 px
  radius, and resting elevation; headings and whitespace still carry the
  large-scale structure.
- Tables: 36 px rows, sticky header, right-aligned numbers, zebra off, row hover
  at 4% ink.

**Motion.** None on page load. Filter and toggle changes update in place with a
120 ms opacity crossfade on charts; tables re-render without animation.
`prefers-reduced-motion` disables the crossfade.

**Charts (Visx).** Axes in `--ink-muted`, 1 px; gridlines only on the value axis;
no chart titles inside the SVG (the heading above carries it); direct labels at
bar ends instead of legends where possible; the responder/non-responder legend
appears once per page, above the small multiples.

**Avoid** — patterns that read as templated and are out of scope here: KPI tile
grids; heavy decorative drop shadows; cream backgrounds with a
terracotta accent; near-black-on-black with a neon accent; ALL-CAPS eyebrow
labels; middle-dot metadata strings; arrows appended to link text; significance
stars; rainbow categorical palettes; a chart library's default theme; icons as
decoration; entrance animations.

## 7. Copy

- Sentence case everywhere. Plain verbs: "Download CSV", "Clear filters", "Show
  per subject".
- Name things as the user knows them: "responders", not "response = yes";
  "day 7", not "t7"; population display names ("CD4 T cells") in headings,
  machine names (`cd4_t_cell`) in the Part 2 table where the assignment fixes
  them.
- Finding template (`/response`), filled from the statistics object:

  > Across {n_samples} PBMC samples from {n_subjects} melanoma patients on
  > miraclib, {list of populations with p < α, or "no population"} differ(s) in
  > relative frequency between responders and non-responders at p < {α}
  > (Mann–Whitney U). After Benjamini–Hochberg adjustment across
  > {n_populations} populations, {list with q < α, or "none"} remain(s)
  > significant. {Per-subject sentence.} {Time-stratified sentence.}

- Empty state: "No samples match these filters." with a "Clear filters" action.
- Error state when the bundle is missing: "No data bundle found. Run
  `make pipeline` to generate it." — the fix, not an apology.

## 8. Accessibility and quality floor

- Every chart has a "Show as table" toggle rendering the same data.
- All controls keyboard-reachable with a visible `--focus` ring; tab order
  follows reading order.
- Colour is never the only carrier of meaning: group labels appear on axes and
  in tooltips; box plots are also distinguished by position.
- Contrast ≥ 4.5:1 for text, ≥ 3:1 for chart marks against `--panel`.
- Responsive to 360 px wide: small multiples wrap, tables scroll horizontally
  with a pinned first column, the cohort strip stacks.
- Lighthouse accessibility ≥ 95 on every route; Playwright checks the toggles
  and the table fallbacks.

## 9. Open questions

None blocking. Two nice-to-haves recorded for later: a per-subject trajectory
view (each subject's three time points as a line, split by response) and a
downloadable PDF of the response page. Neither is required by the assignment.
