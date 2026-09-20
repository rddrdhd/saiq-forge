# Wiki Schema

## Identity
- **Path:** /pfs/lustrep3/scratch/project_465003214/rkovaleo/saiq-forge2/saiq-forge
- **Domain:** SAIQ-Forge — a modular, config-driven framework for real-time
  network anomaly detection, fusing four feature modalities (temporal,
  topological, geographical, behavioral) and five detector classes
  (statistical, classical ML, deep learning, graph-based, quantum/VQC).
  Built and benchmarked on LUMI (AMD MI250X, Slurm, ROCm) and Karolina,
  with quantum access to a 24-qubit processor (VLQ) via IT4Innovations'
  LEXIS platform. This repo is on an intentionally emptied `rewrite`
  branch — the wiki documents the framework's architecture, design
  decisions, module docs, and experiment logs as code is (re)written here.
- **Source types:** thesis/paper excerpts (from the sibling `a0_THESIS`
  and `a1_IEEE_TQE` submodules), papers/URLs cited by the thesis, code
  files as they're written, LUMI/IT4I documentation, experiment logs.
- **Created:** 2026-09-20

## Page Frontmatter
Every wiki page must start with:
---
title: <page title>
category: <one of the Index Categories below>
summary: <one-line description — becomes this page's index entry>
tags: [tag1, tag2]
sources: [source-slug1]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

`category` and `summary` drive index generation (see **Index Generation** below);
`category` must match one of the wiki's Index Categories. `created` is set once when the
page is first written and never changes; `updated` bumps on every edit.

## Cross-References
- **link_style:** markdown
- **link_style_rules:** config/link-style.md
- See `config/link-style.md` for the exact emit and parse rules. Every wiki skill
  reads that file to decide how to write new cross-references and how to scan
  existing ones.

Chosen because this repo is public on GitHub and browsed directly there and
in plain editors/VS Code preview, not assumed to be opened in Obsidian.

## Concept Identity

The slug **is** the concept's identity — there is no separate id. A concept is the
page at `wiki/pages/<slug>.md`; everything that links to it uses the markdown
cross-reference form from `config/link-style.md`. This only
works if the link graph is trustworthy, so two rules hold everywhere links are written:

1. **Links are verified, never invented.** Before writing any link, the slug must
   resolve to an existing `wiki/pages/<slug>.md` **or** to a page being created in the
   same operation. List the existing page set first (`ls wiki/pages/`); never emit a
   link to a slug you have not confirmed. A link that resolves to nothing is a
   hallucinated link — the failure this discipline exists to prevent.

2. **Homonyms get qualified slugs.** When a new concept collides with an existing slug
   for a *different* sense, qualify both with a discriminator rather than overloading
   one page — e.g. `phase-4-quantum-exploration` vs. a hypothetical unrelated
   `phase-4-other-sense`, or `vqc-classifier` vs. `vqc-hardware-access`.
   Pick the narrowest discriminator that disambiguates. `wiki-lint` warns when slugs
   sharing a base token look like an unintended collision.

Consolidating two pages that turn out to be the same concept (merge), or separating one
overloaded page into qualified pages (split), is the job of the `wiki-merge` skill.

## Citations

Cite every non-common-knowledge factual claim. "Common knowledge" = uncontroversial,
undergraduate-level facts in this wiki's domain (network anomaly detection, HPC, quantum
computing). Granularity is paragraph or claim, never per-sentence. If you cannot produce
a citation in one of the forms below, find one, weaken the claim, or drop it.

Format: Markdown footnotes. Two citation kinds, three valid targets.

**Quote citation** (preferred):
```
The framework fuses four feature modalities.[^1]

[^1]: [[thesis-methodology](pages/thesis-methodology.md)] §Data Representation and Feature Extraction L242-244 — "temporal, topological, geographical, and behavioral"
```

**Synthesis citation** (when no single quote captures the claim):
```
The quantum component is scoped as exploratory, not a primary contribution.[^2]

[^2]: [[thesis-methodology](pages/thesis-methodology.md)] §Quantum-Inspired Component [synthesis] L390-435 — the whole subsection frames VQC work as a methodologically systematic comparison, not a production deliverable
```

`L242-244` / `L390-435` are line ranges in the raw source file. For a quote they mark
the lines the quote is taken from; for a synthesis they mark the block being summarized.

Three rules for every footnote:

1. **The cited target is one of three forms:**
   - A slug reference to a source-type wiki page, written in the wiki's
     markdown link style (preferred for sources ingested via `wiki-ingest`)
   - `raw/<file>` or `assets/<file>` — a path to a local file (for drive-by
     citations where a synthesis page isn't worth creating)
   - `<URL>` — a live URL, tweet, or ephemeral source (no local copy required)

   Never cite entity, concept, or analysis pages — those are syntheses, not sources.

2. **A locator is present.** Always a semantic locator: `§<section>`, `p.<n>`,
   `[HH:MM:SS]` for transcripts, URL anchor for web, or `(YYYY-MM-DD)` for dated posts.

   **Plus a line-range when the source is text-addressable.** If the resolved raw
   file is markdown, plaintext, code, or cached HTML (this includes the ingested
   `.tex` sources from the thesis/paper submodules), append a line-range token after
   the semantic locator:

   - `L<start>-<end>` — a range, e.g. `L142-145`
   - `L<n>` — a single line, e.g. `L142`
   - `L142-145,L201-203` — disjoint ranges

   The line range refers to lines in the **raw source file** resolved from the target
   (a page's `**Source:**` raw path; or a direct `raw/<file>`/`assets/<file>`).
   `raw/` is immutable, so these line numbers are stable references.

   A line-range is **required** for text-addressable sources and applies to BOTH
   citation kinds. **Exempt** (semantic locator only, no `L…`): PDFs, transcripts, and
   live URLs with no local cached copy.

3. **Either a verbatim quote, or the `[synthesis]` tag plus a description** of
   what the cited range supports. No third option.

**Drive-by citation examples:**
```
[^3]: raw/lumi-storage-docs.md — "no backups for any storage systems of LUMI"
[^4]: https://docs.lumi-supercomputer.eu/storage/ (2026-09-20) — data storage options
```

## Cross-Model Review

`wiki-audit strong` runs a second-opinion pass with a different-provider model and
stamps the audited page with an optional `review:` frontmatter block:
```
review:
  model: codex          # gemini | claude-sonnet
  provider: openai      # google | anthropic
  date: YYYY-MM-DD
  status: clean         # or: disputed
  findings: 2           # present only when status: disputed
```
- `status: clean` — the reviewer surfaced no disagreement with the normal audit.
- `status: disputed` — the reviewer flagged overreach or a contradiction the normal
  audit missed; `findings:` carries the count. The detail lives in the (local-only)
  audit report.
- `provider: anthropic` (the `claude-sonnet` fallback) means no different-provider CLI
  was available, so the check is same-provider and weaker.

This block is optional and is added only by `wiki-audit strong`. Pages never need it to
be valid.

## Contradiction Check

`wiki-ingest` runs a cheap contradiction check on the pages each ingest touches, before it
commits. It is a **gate, not an annotation**: every page that lands in git is clean.

- **Scope — touched neighbors only.** The check compares the pages an ingest wrote or
  edited against (a) themselves and (b) the pages that ingest already read (the entity /
  concept pages it updated and the neighbor pages from its backlink audit). It does NOT
  re-read the whole wiki — a conflict with a distant, untouched page is left to the
  periodic `wiki-lint` sweep.
- **Blocking vs. soft.** A **blocking** contradiction is a real factual conflict on the same
  entity under the same scope — incompatible dates, counts, names, or mutually-exclusive
  claims. A **soft** tension (differing emphasis, values within plausible version /
  measurement variance, claims that hold under different scope) is not a conflict.
  For this wiki specifically: differing numbers between the thesis's full Phase 4
  protocol and its "Preliminary Pilot (Reduced Scale)" results are a *soft* tension by
  design (the thesis itself frames the pilot as deliberately reduced-scale), not a
  blocking contradiction — don't flag them as one.
- **The transient blocker flag.** When a blocking contradiction is found, a single line is
  written to the affected page's frontmatter and the ingest stops before committing:
  ```yaml
  contradiction-check: failed — <one-line reason naming the counterpart [[slug]] or "internal">
  ```
  The machine-readable token is the literal `contradiction-check: failed`. It exists ONLY
  while the conflict is unresolved; resolving the conflict **removes the line**. A committed
  page never carries it — there is no `passed` stamp, no severity history, nothing. Absence
  of the flag is the only "clean" state.
- **Soft tensions are surfaced, not recorded** — mentioned in the ingest summary so you can
  act if you wish, but never persisted and never blocking.

This flag is also what the **Pre-commit Gate** below scans staged files for.

## Pre-commit Gate

`bin/hooks/pre-commit` (wired via `git config core.hooksPath bin/hooks`) runs **two**
deterministic gates before every commit — no LLM:

1. **`bin/check-contradictions.py`** — scans the **staged** content of `wiki/pages/*.md`,
   frontmatter only, and **blocks the commit** if any page still carries a
   `contradiction-check: failed` flag. Backstop to the skill-level hold in `wiki-ingest`
   step 7b; on a healthy wiki it never fires. Resolve the contradiction and remove the
   `contradiction-check:` line, then re-stage.
2. **`bin/lint-mechanical.py --staged`** — scans the staged pages for **structural**
   problems and **blocks the commit** on any: missing required frontmatter, a broken
   link, or a slug collision (a bare slug clashing with a qualified one). Fix the page
   and re-stage.

- **Fresh clone (including a fresh clone of this submodule):** `core.hooksPath` is
  repo-local config and is not cloned — re-run `git config core.hooksPath bin/hooks`
  once after cloning.
- **Override** an intentional commit with `git commit --no-verify`.

## Operation Log & Commit Convention
Operations: init, ingest, query, update, lint, audit, merge, split

**Git wiki — the git history is the operation log.** Render the human log on demand
with `python bin/render-log.py`.

The suggested subject line follows Conventional Commits (this repo's existing history
on `danger`/`master` used free-form subjects with no detected convention, so the
default applies), choosing the type by operation:

   | Operation        | Type                                  |
   |------------------|---------------------------------------|
   | init             | `chore`                               |
   | ingest           | `docs`                                |
   | update           | `docs`                                |
   | query (saved)    | `docs`                                |
   | lint             | `fix` if fixes applied, else `chore`  |
   | audit            | `fix` if fixes applied, else `chore`  |
   | merge / split    | `refactor`                            |

**Always append a `Wiki-Op:` trailer**, whatever the subject style — it is what
`render-log.py` keys on, decoupling the log from the subject convention. Which pages
changed is read from the commit diff, so no `Pages:` trailer is needed.
```
docs: summarize Attention Is All You Need

Wiki-Op: ingest
```

## Index Generation
`wiki/index.md` is a generated, gitignored artifact — never hand-edit it. It is rebuilt
from page frontmatter by `bin/generate-index.py`:
- Run `python bin/generate-index.py` (or `python3`) **before reading the index**, and
  **after** any operation that adds, removes, renames, or re-categorizes a page.
- The generator groups pages by their `category` frontmatter, in the order categories are
  listed under **Index Categories** below; within a category it lists pages newest-first
  by `created`. Each entry is `- [[slug]] — summary _(created)_`.
- Pages whose filename matches `audit-*.md` are excluded (gitignored local-only
  artifacts). A page with an unrecognized or missing `category` lands in an
  `Uncategorized` section.

## Index Categories
Sources
Concepts
Modules
Decisions
Experiments

- **Sources**: ingested source material (thesis chapters/sections, papers,
  LUMI/IT4I docs) — what wiki-ingest creates from raw/ material.
- **Concepts**: recurring vocabulary that many pages reference — RQ1–RQ5,
  Phases 0–5, the four feature modalities, the five detector classes,
  dataset A/B/C definitions. Canonical definitions trace back to
  `a0_THESIS/Body.tex`; these pages should cite it, not restate it as if
  original to this repo.
- **Modules**: this codebase's own architecture — feature extractors,
  detector implementations, the pipeline/orchestration layer, the
  LUMI/LEXIS/VLQ integration layer — as they're (re)written on `rewrite`.
- **Decisions**: design decisions and their rationale/tradeoffs (e.g. why
  config-driven, why a lightweight venv over conda for the VLQ job
  scripts, why a given window size default) — the "why," which code
  comments in this repo deliberately don't carry (see `../CLAUDE.md`'s
  code-style note).
- **Experiments**: phase-by-phase progress and results as they're run —
  intended to stay in sync with, but not duplicate, the thesis's own
  Experimental Plan section.

## Conventions
- raw/ is immutable — skills never modify it. Some entries under raw/ are
  symlinks to a private location outside this repo (`../wiki-raw/`, in the
  outer `saiq-forge2` workspace) rather than real committed files — this
  applies specifically to sources drawn from the still-unpublished thesis
  or article, and is invisible to `git status` here by design (see
  `../CLAUDE.md`). They resolve as normal files for every wiki tool; only
  their presence in *this* repo's git history is what's suppressed.
  Genuinely public sources (LUMI/IT4I docs, published papers) are real,
  committed files here as normal — the symlink treatment is the exception,
  not the default.
- operation log: git wikis record each op as a commit (see Operation Log & Commit Convention) and render it with bin/render-log.py; non-git wikis append to log.md (append-only, never rewritten)
- index.md is GENERATED by bin/generate-index.py and is gitignored — never hand-edit it; set page frontmatter (category, summary) and regenerate instead
- All pages live flat in wiki/pages/ — no subdirectories
- overview.md reflects the current synthesis across all sources
- Cross-reference and citation slug-targets follow `config/link-style.md` —
  every skill reads it before writing or scanning links
- contradiction check: ingest gates on blocking contradictions in touched pages via a transient `contradiction-check: failed` flag, removed before commit — committed pages are always clean (see Contradiction Check)
- pre-commit gate: this git wiki runs bin/hooks/pre-commit (via core.hooksPath) → bin/check-contradictions.py, which blocks any commit staging a page that still carries the flag (see Pre-commit Gate); re-run `git config core.hooksPath bin/hooks` after a fresh clone
- README boundary: wiki pages must not duplicate `../CLAUDE.md` or a future README's operational content (setup, contributing, running). Extract structural/design signals; link to those files for operational content.
