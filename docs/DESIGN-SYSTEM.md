# Design system: Real-time AI Compliance Review Copilot

| | |
|---|---|
| **Status** | Draft v0.1 · 2026-10-05 IST · provisional decisions referenced as D-xx ([PRD §19](PRD.md#19-decisions-log)) |
| **Source** | [`sources/design.md`](sources/design.md) (Design Head), contrast check [`sources/design-contrast.py`](sources/design-contrast.py) → [`sources/design-contrast.json`](sources/design-contrast.json) |
| **Stack** | Next.js 16 · React 19 · TypeScript · Tailwind 4 · Phosphor icons |
| **Related** | [`PRD.md`](PRD.md) · [`ACCEPTANCE-CRITERIA.md`](ACCEPTANCE-CRITERIA.md) (UX criteria are AC-UX-*, AC-STR-*, AC-COL-*) |

No screens or Figma files exist yet. This document is the spec.

---

## 1. Principles

1. **Evidence before conclusions.** A finding reads *clause → control → why → severity*. The exact cited text is one click or one key (`G`) away and is highlighted in the document. Only citation-verified findings are shown; the analysis summary states how many were discarded ("2 findings discarded: citation check failed").
2. **AI output is attributable and reversible.** AI-written text carries an AI marker; the audit log records model, pack version and time. Human edits show a diff against the AI original. Decisions can be undone or superseded with a reason. Nothing is deleted from the trail.
3. **The human decision is final.** The AI proposes, reviewers decide. No auto-accept at any confidence. The final report contains only human-decided findings; sign-off is a named Owner's action.
4. **Honest confidence.** Bands (High / Medium / Low) with a reason, never a precise-looking percentage. Low confidence is made louder, not hidden, and never moved out of its severity group (D-01).
5. **The audit trail is visible.** Who, what, when and why is shown on the finding and in the project log. Reasons are required for reject, escalate, severity change, change-of-decision and override.
6. **Calm density, live without noise.** Compact rows, neutral palette, colour reserved for severity and state. No auto-scroll, no focus jumps, no toast per streamed finding.
7. **Never colour alone.** Every severity and status uses text label + icon + shape; colour is the fourth cue.

## 2. Tokens

### 2.1 Colour rules
- Neutral slate base (hue 255) and **one accent, indigo (hue 272)**, for actions, selection and focus. Indigo does not collide with any severity hue.
- **Severity hues:** critical red (25), high orange (45–50), medium amber (75–92), low cyan (220), info neutral.
- **Decision state:** success green (150) for accepted/resolved; pending neutral for "Needs decision". `info` and `pending` share the neutral value but never share a slot, and differ by icon and shape.
- **AI tint** (`--ai-tint`, faint violet) marks AI-authored blocks (rationale, remediation, summary). Human-edited text drops the tint.
- **Severity variants:** `-subtle` = badge/row background; `-hl` = in-document highlight (stronger, text on it still ≥ 4.5:1); `-solid` = critical and high badges only.
- `--border` is decorative. Inputs, checkboxes and toggles use `--border-strong` (≥ 3:1, WCAG 1.4.11).
- Hex values are fallbacks; OKLCH values are applied via `@supports`. Values are gamut-fitted to sRGB so both render the same colour.

### 2.2 Token values

| Token | Light OKLCH | Light hex | Dark OKLCH | Dark hex |
|---|---|---|---|---|
| `--bg` | `oklch(98.5% 0.002 255)` | `#f9fafb` | `oklch(16.0% 0.008 255)` | `#0b0d11` |
| `--surface` | `oklch(100.0% 0.000 255)` | `#ffffff` | `oklch(20.0% 0.010 255)` | `#13161b` |
| `--surface-2` | `oklch(96.8% 0.004 255)` | `#f3f5f7` | `oklch(23.5% 0.011 255)` | `#1b1e23` |
| `--surface-3` | `oklch(94.0% 0.006 255)` | `#e8ebef` | `oklch(27.5% 0.012 255)` | `#24282e` |
| `--border` | `oklch(91.0% 0.006 255)` | `#dfe1e5` | `oklch(31.0% 0.012 255)` | `#2c3136` |
| `--border-strong` | `oklch(62.0% 0.012 255)` | `#81878d` | `oklch(56.0% 0.015 255)` | `#6f757d` |
| `--text` | `oklch(21.0% 0.015 255)` | `#14191f` | `oklch(96.5% 0.004 255)` | `#f2f4f6` |
| `--text-secondary` | `oklch(40.0% 0.015 255)` | `#424850` | `oklch(82.0% 0.010 255)` | `#c0c4cb` |
| `--text-muted` | `oklch(50.0% 0.014 255)` | `#5e646b` | `oklch(72.0% 0.012 255)` | `#a0a5ac` |
| `--accent` | `oklch(50.0% 0.170 272)` | `#4455c2` | `oklch(76.0% 0.122 272)` | `#96acff` |
| `--accent-hover` | `oklch(44.0% 0.160 272)` | `#3745a9` | `oklch(82.0% 0.089 272)` | `#b0c1ff` |
| `--accent-fg` | `oklch(99.0% 0.003 272)` | `#fbfcfe` | `oklch(18.0% 0.040 272)` | `#0b1023` |
| `--accent-text` | `oklch(49.0% 0.170 272)` | `#4252bf` | `oklch(78.0% 0.111 272)` | `#9eb3ff` |
| `--accent-subtle` | `oklch(95.5% 0.021 272)` | `#ebf0ff` | `oklch(29.0% 0.060 272)` | `#212949` |
| `--accent-subtle-fg` | `oklch(40.0% 0.150 272)` | `#2f3b97` | `oklch(88.0% 0.058 272)` | `#cad6ff` |
| `--focus` | `oklch(55.0% 0.170 272)` | `#5165d3` | `oklch(78.0% 0.111 272)` | `#9eb3ff` |
| `--critical` | `oklch(50.0% 0.190 25)` | `#b71824` | `oklch(74.0% 0.150 25)` | `#fb817a` |
| `--critical-solid` | `oklch(50.0% 0.190 25)` | `#b71824` | `oklch(70.0% 0.170 25)` | `#f66d67` |
| `--critical-on-solid` | `oklch(99.0% 0.000 0)` | `#fcfcfc` | `oklch(17.0% 0.030 25)` | `#1b0a09` |
| `--critical-subtle` | `oklch(96.0% 0.019 25)` | `#ffedeb` | `oklch(28.0% 0.060 25)` | `#421c19` |
| `--critical-hl` | `oklch(92.0% 0.040 25)` | `#fedbd7` | `oklch(34.0% 0.080 25)` | `#5a2522` |
| `--high` | `oklch(52.0% 0.148 45)` | `#ab4501` | `oklch(78.0% 0.130 50)` | `#fa9d68` |
| `--high-solid` | `oklch(55.0% 0.157 45)` | `#b84b01` | `oklch(76.0% 0.140 50)` | `#f7945a` |
| `--high-on-solid` | `oklch(99.0% 0.000 0)` | `#fcfcfc` | `oklch(17.0% 0.030 50)` | `#1a0b04` |
| `--high-subtle` | `oklch(96.2% 0.021 50)` | `#ffefe6` | `oklch(28.0% 0.050 50)` | `#3c2111` |
| `--high-hl` | `oklch(92.0% 0.048 55)` | `#ffddc7` | `oklch(34.0% 0.070 50)` | `#542c13` |
| `--medium` | `oklch(50.0% 0.105 75)` | `#865901` | `oklch(84.0% 0.130 85)` | `#f1c45e` |
| `--medium-subtle` | `oklch(96.5% 0.040 90)` | `#fef3d6` | `oklch(28.0% 0.050 80)` | `#362607` |
| `--medium-hl` | `oklch(93.0% 0.080 92)` | `#fbe7ab` | `oklch(35.0% 0.070 85)` | `#4b3702` |
| `--low` | `oklch(50.0% 0.091 220)` | `#006f87` | `oklch(80.0% 0.100 220)` | `#6ccdea` |
| `--low-subtle` | `oklch(96.2% 0.020 220)` | `#e5f6fc` | `oklch(28.0% 0.040 220)` | `#0e2d36` |
| `--low-hl` | `oklch(92.5% 0.045 220)` | `#c6eefb` | `oklch(34.0% 0.060 220)` | `#043f4d` |
| `--info` | `oklch(46.0% 0.020 255)` | `#515963` | `oklch(80.0% 0.015 255)` | `#b7bec7` |
| `--info-subtle` | `oklch(95.5% 0.006 255)` | `#edf0f4` | `oklch(27.0% 0.012 255)` | `#23272c` |
| `--success` | `oklch(48.0% 0.120 150)` | `#197037` | `oklch(80.0% 0.150 150)` | `#6ed889` |
| `--success-subtle` | `oklch(96.0% 0.030 150)` | `#e4f8e7` | `oklch(27.0% 0.050 150)` | `#122d19` |
| `--pending` | `oklch(46.0% 0.020 255)` | `#515963` | `oklch(80.0% 0.015 255)` | `#b7bec7` |
| `--pending-subtle` | `oklch(96.0% 0.006 255)` | `#eff2f6` | `oklch(27.0% 0.012 255)` | `#23272c` |
| `--ai-tint` | `oklch(97.0% 0.012 300)` | `#f6f3fc` | `oklch(23.0% 0.025 300)` | `#1f1a27` |

### 2.3 Tailwind 4 `@theme` block

From the design input, unchanged. Design notes it compiles on Tailwind 4.3.3.

```css
@import "tailwindcss";

:root, [data-theme="light"] {
  --bg: #f9fafb;
  --surface: #ffffff;
  --surface-2: #f3f5f7;
  --surface-3: #e8ebef;
  --border: #dfe1e5;
  --border-strong: #81878d;
  --text: #14191f;
  --text-secondary: #424850;
  --text-muted: #5e646b;
  --accent: #4455c2;
  --accent-hover: #3745a9;
  --accent-fg: #fbfcfe;
  --accent-text: #4252bf;
  --accent-subtle: #ebf0ff;
  --accent-subtle-fg: #2f3b97;
  --focus: #5165d3;
  --critical: #b71824;
  --critical-solid: #b71824;
  --critical-on-solid: #fcfcfc;
  --critical-subtle: #ffedeb;
  --critical-hl: #fedbd7;
  --high: #ab4501;
  --high-solid: #b84b01;
  --high-on-solid: #fcfcfc;
  --high-subtle: #ffefe6;
  --high-hl: #ffddc7;
  --medium: #865901;
  --medium-subtle: #fef3d6;
  --medium-hl: #fbe7ab;
  --low: #006f87;
  --low-subtle: #e5f6fc;
  --low-hl: #c6eefb;
  --info: #515963;
  --info-subtle: #edf0f4;
  --success: #197037;
  --success-subtle: #e4f8e7;
  --pending: #515963;
  --pending-subtle: #eff2f6;
  --ai-tint: #f6f3fc;
}
@supports (color: oklch(0% 0 0)) {
  :root, [data-theme="light"] {
    --bg: oklch(98.5% 0.002 255);
    --surface: oklch(100.0% 0.000 255);
    --surface-2: oklch(96.8% 0.004 255);
    --surface-3: oklch(94.0% 0.006 255);
    --border: oklch(91.0% 0.006 255);
    --border-strong: oklch(62.0% 0.012 255);
    --text: oklch(21.0% 0.015 255);
    --text-secondary: oklch(40.0% 0.015 255);
    --text-muted: oklch(50.0% 0.014 255);
    --accent: oklch(50.0% 0.170 272);
    --accent-hover: oklch(44.0% 0.160 272);
    --accent-fg: oklch(99.0% 0.003 272);
    --accent-text: oklch(49.0% 0.170 272);
    --accent-subtle: oklch(95.5% 0.021 272);
    --accent-subtle-fg: oklch(40.0% 0.150 272);
    --focus: oklch(55.0% 0.170 272);
    --critical: oklch(50.0% 0.190 25);
    --critical-solid: oklch(50.0% 0.190 25);
    --critical-on-solid: oklch(99.0% 0.000 0);
    --critical-subtle: oklch(96.0% 0.019 25);
    --critical-hl: oklch(92.0% 0.040 25);
    --high: oklch(52.0% 0.148 45);
    --high-solid: oklch(55.0% 0.157 45);
    --high-on-solid: oklch(99.0% 0.000 0);
    --high-subtle: oklch(96.2% 0.021 50);
    --high-hl: oklch(92.0% 0.048 55);
    --medium: oklch(50.0% 0.105 75);
    --medium-subtle: oklch(96.5% 0.040 90);
    --medium-hl: oklch(93.0% 0.080 92);
    --low: oklch(50.0% 0.091 220);
    --low-subtle: oklch(96.2% 0.020 220);
    --low-hl: oklch(92.5% 0.045 220);
    --info: oklch(46.0% 0.020 255);
    --info-subtle: oklch(95.5% 0.006 255);
    --success: oklch(48.0% 0.120 150);
    --success-subtle: oklch(96.0% 0.030 150);
    --pending: oklch(46.0% 0.020 255);
    --pending-subtle: oklch(96.0% 0.006 255);
    --ai-tint: oklch(97.0% 0.012 300);
  }
}
[data-theme="dark"] {
  --bg: #0b0d11;
  --surface: #13161b;
  --surface-2: #1b1e23;
  --surface-3: #24282e;
  --border: #2c3136;
  --border-strong: #6f757d;
  --text: #f2f4f6;
  --text-secondary: #c0c4cb;
  --text-muted: #a0a5ac;
  --accent: #96acff;
  --accent-hover: #b0c1ff;
  --accent-fg: #0b1023;
  --accent-text: #9eb3ff;
  --accent-subtle: #212949;
  --accent-subtle-fg: #cad6ff;
  --focus: #9eb3ff;
  --critical: #fb817a;
  --critical-solid: #f66d67;
  --critical-on-solid: #1b0a09;
  --critical-subtle: #421c19;
  --critical-hl: #5a2522;
  --high: #fa9d68;
  --high-solid: #f7945a;
  --high-on-solid: #1a0b04;
  --high-subtle: #3c2111;
  --high-hl: #542c13;
  --medium: #f1c45e;
  --medium-subtle: #362607;
  --medium-hl: #4b3702;
  --low: #6ccdea;
  --low-subtle: #0e2d36;
  --low-hl: #043f4d;
  --info: #b7bec7;
  --info-subtle: #23272c;
  --success: #6ed889;
  --success-subtle: #122d19;
  --pending: #b7bec7;
  --pending-subtle: #23272c;
  --ai-tint: #1f1a27;
}
@supports (color: oklch(0% 0 0)) {
  [data-theme="dark"] {
    --bg: oklch(16.0% 0.008 255);
    --surface: oklch(20.0% 0.010 255);
    --surface-2: oklch(23.5% 0.011 255);
    --surface-3: oklch(27.5% 0.012 255);
    --border: oklch(31.0% 0.012 255);
    --border-strong: oklch(56.0% 0.015 255);
    --text: oklch(96.5% 0.004 255);
    --text-secondary: oklch(82.0% 0.010 255);
    --text-muted: oklch(72.0% 0.012 255);
    --accent: oklch(76.0% 0.122 272);
    --accent-hover: oklch(82.0% 0.089 272);
    --accent-fg: oklch(18.0% 0.040 272);
    --accent-text: oklch(78.0% 0.111 272);
    --accent-subtle: oklch(29.0% 0.060 272);
    --accent-subtle-fg: oklch(88.0% 0.058 272);
    --focus: oklch(78.0% 0.111 272);
    --critical: oklch(74.0% 0.150 25);
    --critical-solid: oklch(70.0% 0.170 25);
    --critical-on-solid: oklch(17.0% 0.030 25);
    --critical-subtle: oklch(28.0% 0.060 25);
    --critical-hl: oklch(34.0% 0.080 25);
    --high: oklch(78.0% 0.130 50);
    --high-solid: oklch(76.0% 0.140 50);
    --high-on-solid: oklch(17.0% 0.030 50);
    --high-subtle: oklch(28.0% 0.050 50);
    --high-hl: oklch(34.0% 0.070 50);
    --medium: oklch(84.0% 0.130 85);
    --medium-subtle: oklch(28.0% 0.050 80);
    --medium-hl: oklch(35.0% 0.070 85);
    --low: oklch(80.0% 0.100 220);
    --low-subtle: oklch(28.0% 0.040 220);
    --low-hl: oklch(34.0% 0.060 220);
    --info: oklch(80.0% 0.015 255);
    --info-subtle: oklch(27.0% 0.012 255);
    --success: oklch(80.0% 0.150 150);
    --success-subtle: oklch(27.0% 0.050 150);
    --pending: oklch(80.0% 0.015 255);
    --pending-subtle: oklch(27.0% 0.012 255);
    --ai-tint: oklch(23.0% 0.025 300);
  }
}
@theme inline {
  --color-bg: var(--bg);
  --color-surface: var(--surface);
  --color-surface-2: var(--surface-2);
  --color-surface-3: var(--surface-3);
  --color-border: var(--border);
  --color-border-strong: var(--border-strong);
  --color-text: var(--text);
  --color-text-secondary: var(--text-secondary);
  --color-text-muted: var(--text-muted);
  --color-accent: var(--accent);
  --color-accent-hover: var(--accent-hover);
  --color-accent-fg: var(--accent-fg);
  --color-accent-text: var(--accent-text);
  --color-accent-subtle: var(--accent-subtle);
  --color-accent-subtle-fg: var(--accent-subtle-fg);
  --color-focus: var(--focus);
  --color-critical: var(--critical);
  --color-critical-solid: var(--critical-solid);
  --color-critical-on-solid: var(--critical-on-solid);
  --color-critical-subtle: var(--critical-subtle);
  --color-critical-hl: var(--critical-hl);
  --color-high: var(--high);
  --color-high-solid: var(--high-solid);
  --color-high-on-solid: var(--high-on-solid);
  --color-high-subtle: var(--high-subtle);
  --color-high-hl: var(--high-hl);
  --color-medium: var(--medium);
  --color-medium-subtle: var(--medium-subtle);
  --color-medium-hl: var(--medium-hl);
  --color-low: var(--low);
  --color-low-subtle: var(--low-subtle);
  --color-low-hl: var(--low-hl);
  --color-info: var(--info);
  --color-info-subtle: var(--info-subtle);
  --color-success: var(--success);
  --color-success-subtle: var(--success-subtle);
  --color-pending: var(--pending);
  --color-pending-subtle: var(--pending-subtle);
  --color-ai-tint: var(--ai-tint);
}

@theme inline {
  --font-sans: var(--font-inter), ui-sans-serif, system-ui, sans-serif;
  --font-serif: var(--font-source-serif), ui-serif, Georgia, serif;
  --font-mono: var(--font-jetbrains), ui-monospace, monospace;

  --text-caption: 0.75rem;    --text-caption--line-height: 1rem;
  --text-label: 0.8125rem;    --text-label--line-height: 1.125rem;   --text-label--font-weight: 500;
  --text-body-sm: 0.875rem;   --text-body-sm--line-height: 1.25rem;
  --text-body: 0.9375rem;     --text-body--line-height: 1.5rem;
  --text-doc: 1rem;           --text-doc--line-height: 1.75rem;
  --text-title-sm: 1rem;      --text-title-sm--line-height: 1.5rem;  --text-title-sm--font-weight: 600;
  --text-title: 1.25rem;      --text-title--line-height: 1.75rem;    --text-title--font-weight: 600;
  --text-headline: 1.75rem;   --text-headline--line-height: 2.25rem; --text-headline--font-weight: 600;

  --radius-xs: 4px; --radius-sm: 6px; --radius-md: 8px; --radius-lg: 12px;

  --shadow-1: var(--elev-1); --shadow-2: var(--elev-2); --shadow-3: var(--elev-3);

  --ease-out: cubic-bezier(0.2, 0.8, 0.2, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
}

:root {
  --elev-1: 0 1px 2px oklch(0.2 0.015 255 / 0.06);
  --elev-2: 0 1px 2px oklch(0.2 0.015 255 / 0.05), 0 6px 16px -4px oklch(0.2 0.015 255 / 0.12);
  --elev-3: 0 4px 8px oklch(0.2 0.015 255 / 0.06), 0 20px 40px -12px oklch(0.2 0.015 255 / 0.22);
  --duration-fast: 120ms; --duration-base: 200ms; --duration-slow: 320ms;
  --motion-ok: 1;
}
[data-theme="dark"] {
  --elev-1: 0 1px 2px oklch(0 0 0 / 0.4);
  --elev-2: 0 1px 2px oklch(0 0 0 / 0.4), 0 8px 20px -6px oklch(0 0 0 / 0.55);
  --elev-3: 0 4px 8px oklch(0 0 0 / 0.45), 0 24px 48px -12px oklch(0 0 0 / 0.65);
}
@media (prefers-reduced-motion: reduce) {
  :root { --duration-fast: 0ms; --duration-base: 0ms; --duration-slow: 0ms; --motion-ok: 0; }
}
@utility focus-ring { outline: 2px solid var(--focus); outline-offset: 2px; }
```

Fonts load via `next/font/google` (`Inter`, `Source_Serif_4`, `JetBrains_Mono`) with `variable: "--font-inter" | "--font-source-serif" | "--font-jetbrains"`. Do not name a `next/font` variable `--font-sans`; that creates a self-reference inside `@theme`.

## 3. Typography

| Role | Font | Notes |
|---|---|---|
| UI | **Inter** (variable, OFL) | `font-feature-settings: "tnum"` for counts and times |
| Document pane | **Source Serif 4** (variable, OFL) | The document reads as a document, separate from AI and UI chrome |
| IDs, clause refs, control IDs, hashes | **JetBrains Mono** (OFL) | `GDPR Art. 28(3)(a)`, `SOC2 CC6.1`, `ISO27001 A.5.15`, `F-0142` |

| Token | Size / line-height (px) | Weight | Use |
|---|---|---|---|
| `text-caption` | 12 / 16 | 400–500 | Timestamps, meta, legal. Minimum size |
| `text-label` | 13 / 18 | 500 | Badges, labels, tabs |
| `text-body-sm` | 14 / 20 | 400 | Finding rows, comments, log |
| `text-body` | 15 / 24 | 400 | Finding detail, report body |
| `text-doc` | 16 / 28 serif | 400 | Document pane, max 72ch |
| `text-title-sm` | 16 / 24 | 600 | Card and panel titles |
| `text-title` | 20 / 28 | 600 | Screen titles |
| `text-headline` | 28 / 36 | 600 | Onboarding, report cover |

Rules: sentence case; nothing below 12 px; uppercase only for ≤ 2-word overlines with +0.04em tracking.

## 4. Colour: severity, state and contrast

### 4.1 Severity encoding (colour is never the only cue)

| Severity | Label (always shown) | Icon / shape (Phosphor) | Badge | Document highlight | Sort |
|---|---|---|---|---|---|
| Critical | `Critical` | Octagon + `!` (`WarningOctagon`) | **Solid**, `critical-on-solid` text | `critical-hl` + 3px solid underline | 1 |
| High | `High` | Triangle (`Warning`) | **Solid** | `high-hl` + 2px solid underline | 2 |
| Medium | `Medium` | Diamond (`Diamond`) | Subtle + 1px border | `medium-hl` + 2px dashed underline | 3 |
| Low | `Low` | Circle (`Circle`) | Subtle | `low-hl` + 1px dotted underline | 4 |
| Info | `Info` | Square-i (`Info`) | Neutral outline | No tint, dotted underline | 5 |

Underline styles (solid / dashed / dotted) keep severity distinguishable in grayscale and for colour-blind users.

### 4.2 Decision state and markers

| State | Label | Icon | Notes |
|---|---|---|---|
| Pending | `Needs decision` | Hollow dashed circle | |
| Accepted | `Accepted` | `CheckCircle` (filled) | `success` colour |
| Rejected | `Rejected` | `XCircle` | Title struck through, dimmed to `text-secondary` |
| Edited | `Accepted · edited` | `PencilSimple` dot | Diff against AI original on expand |
| Escalated | `Escalated to <name>` | `ArrowFatLineUp` | Assignee always named; visible live to everyone; no notification in MVP (D-04) |
| Low confidence (marker, not a state) | `Needs careful review` | Dashed card border + confidence meter `Low` | Stays inside its severity group (D-01) |
| AI-authored | `AI` tag | `--ai-tint` block | Dropped once a human edits the text |

### 4.3 Contrast results (WCAG 2.x AA, computed)

Method: OKLCH → linear sRGB → gamut-fit (reduce chroma) → 8-bit sRGB → WCAG 2.x relative luminance. Text needs 4.5:1. Non-text (focus ring, control borders, solid badges on surface, underline marker on its own highlight) needs 3:1.

**Result: 136 / 136 checks pass (68 pairs × light and dark).** Re-run on 2026-10-05 with `python docs/sources/design-contrast.py`: "136 pairs; fails: 0". Lowest text pair: light `text-muted` on `surface-3`, 5.00:1. Lowest non-text pair: light `border-strong` on `bg`, 3.47:1.

| Foreground | Background | Type (min) | Light | Dark |
|---|---|---|---|---|
| `text` | `bg` | text 4.5 | 16.91 ✓ | 17.64 ✓ |
| `text-secondary` | `bg` | text 4.5 | 8.84 ✓ | 11.11 ✓ |
| `text-muted` | `bg` | text 4.5 | 5.72 ✓ | 7.85 ✓ |
| `text` | `surface` | text 4.5 | 17.67 ✓ | 16.44 ✓ |
| `text-secondary` | `surface` | text 4.5 | 9.23 ✓ | 10.36 ✓ |
| `text-muted` | `surface` | text 4.5 | 5.98 ✓ | 7.31 ✓ |
| `text` | `surface-2` | text 4.5 | 16.17 ✓ | 15.16 ✓ |
| `text-secondary` | `surface-2` | text 4.5 | 8.45 ✓ | 9.55 ✓ |
| `text-muted` | `surface-2` | text 4.5 | 5.47 ✓ | 6.74 ✓ |
| `text` | `surface-3` | text 4.5 | 14.77 ✓ | 13.43 ✓ |
| `text-secondary` | `surface-3` | text 4.5 | 7.72 ✓ | 8.46 ✓ |
| `text-muted` | `surface-3` | text 4.5 | 5.00 ✓ | 5.98 ✓ |
| `accent-fg` | `accent` | text 4.5 | 6.15 ✓ | 8.67 ✓ |
| `accent-fg` | `accent-hover` | text 4.5 | 7.91 ✓ | 10.71 ✓ |
| `accent-text` | `bg` | text 4.5 | 6.30 ✓ | 9.58 ✓ |
| `accent-text` | `surface` | text 4.5 | 6.58 ✓ | 8.93 ✓ |
| `accent-subtle-fg` | `accent-subtle` | text 4.5 | 8.41 ✓ | 9.86 ✓ |
| `text` | `accent-subtle` | text 4.5 | 15.51 ✓ | 12.89 ✓ |
| `critical` | `bg` | text 4.5 | 6.34 ✓ | 7.89 ✓ |
| `critical` | `surface` | text 4.5 | 6.63 ✓ | 7.36 ✓ |
| `critical` | `critical-subtle` | text 4.5 | 5.86 ✓ | 6.04 ✓ |
| `text` | `critical-subtle` | text 4.5 | 15.62 ✓ | 13.49 ✓ |
| `high` | `bg` | text 4.5 | 5.61 ✓ | 9.34 ✓ |
| `high` | `surface` | text 4.5 | 5.86 ✓ | 8.71 ✓ |
| `high` | `high-subtle` | text 4.5 | 5.23 ✓ | 7.12 ✓ |
| `text` | `high-subtle` | text 4.5 | 15.77 ✓ | 13.43 ✓ |
| `medium` | `bg` | text 4.5 | 5.84 ✓ | 11.85 ✓ |
| `medium` | `surface` | text 4.5 | 6.10 ✓ | 11.05 ✓ |
| `medium` | `medium-subtle` | text 4.5 | 5.52 ✓ | 8.90 ✓ |
| `text` | `medium-subtle` | text 4.5 | 15.99 ✓ | 13.25 ✓ |
| `low` | `bg` | text 4.5 | 5.55 ✓ | 10.70 ✓ |
| `low` | `surface` | text 4.5 | 5.80 ✓ | 9.98 ✓ |
| `low` | `low-subtle` | text 4.5 | 5.22 ✓ | 7.99 ✓ |
| `text` | `low-subtle` | text 4.5 | 15.92 ✓ | 13.16 ✓ |
| `info` | `bg` | text 4.5 | 6.79 ✓ | 10.37 ✓ |
| `info` | `surface` | text 4.5 | 7.10 ✓ | 9.67 ✓ |
| `info` | `info-subtle` | text 4.5 | 6.21 ✓ | 8.01 ✓ |
| `text` | `info-subtle` | text 4.5 | 15.46 ✓ | 13.62 ✓ |
| `success` | `bg` | text 4.5 | 5.89 ✓ | 10.97 ✓ |
| `success` | `surface` | text 4.5 | 6.15 ✓ | 10.23 ✓ |
| `success` | `success-subtle` | text 4.5 | 5.53 ✓ | 8.37 ✓ |
| `text` | `success-subtle` | text 4.5 | 15.88 ✓ | 13.46 ✓ |
| `pending` | `bg` | text 4.5 | 6.79 ✓ | 10.37 ✓ |
| `pending` | `surface` | text 4.5 | 7.10 ✓ | 9.67 ✓ |
| `pending` | `pending-subtle` | text 4.5 | 6.32 ✓ | 8.01 ✓ |
| `text` | `pending-subtle` | text 4.5 | 15.73 ✓ | 13.62 ✓ |
| `text` | `critical-hl` | text 4.5 | 13.74 ✓ | 11.06 ✓ |
| `text` | `high-hl` | text 4.5 | 13.81 ✓ | 10.90 ✓ |
| `text` | `medium-hl` | text 4.5 | 14.40 ✓ | 10.31 ✓ |
| `text` | `low-hl` | text 4.5 | 14.32 ✓ | 10.45 ✓ |
| `critical-on-solid` | `critical-solid` | text 4.5 | 6.46 ✓ | 6.67 ✓ |
| `high-on-solid` | `high-solid` | text 4.5 | 5.06 ✓ | 8.54 ✓ |
| `text` | `ai-tint` | text 4.5 | 16.11 ✓ | 15.42 ✓ |
| `text-secondary` | `ai-tint` | text 4.5 | 8.42 ✓ | 9.71 ✓ |
| `focus` | `bg` | non-text 3.0 | 4.84 ✓ | 9.58 ✓ |
| `focus` | `surface` | non-text 3.0 | 5.06 ✓ | 8.93 ✓ |
| `focus` | `surface-2` | non-text 3.0 | 4.63 ✓ | 8.23 ✓ |
| `focus` | `surface-3` | non-text 3.0 | 4.23 ✓ | 7.30 ✓ |
| `focus` | `accent-subtle` | non-text 3.0 | 4.44 ✓ | 7.00 ✓ |
| `border-strong` | `bg` | non-text 3.0 | 3.47 ✓ | 4.18 ✓ |
| `border-strong` | `surface` | non-text 3.0 | 3.63 ✓ | 3.90 ✓ |
| `accent` | `surface` | non-text 3.0 | 6.32 ✓ | 8.32 ✓ |
| `critical-solid` | `surface` | non-text 3.0 | 6.63 ✓ | 6.30 ✓ |
| `high-solid` | `surface` | non-text 3.0 | 5.19 ✓ | 8.06 ✓ |
| `critical` | `critical-hl` | non-text 3.0 | 5.15 ✓ | 4.95 ✓ |
| `high` | `high-hl` | non-text 3.0 | 4.58 ✓ | 5.78 ✓ |
| `medium` | `medium-hl` | non-text 3.0 | 4.97 ✓ | 6.93 ✓ |
| `low` | `low-hl` | non-text 3.0 | 4.70 ✓ | 6.34 ✓ |

**Approved-pairs rule.** Pairs not in this table are not approved: e.g. severity text on another severity's highlight, `text-muted` on any `-hl`, or any text on `-solid` other than its `-on-solid`. Where highlights overlap, use the highest severity's `-hl`, never a blended mix (blends are not checked). Accepted-finding highlights mix `-hl` 60% toward `surface`, which only raises contrast with `text`.

## 5. Spacing, radius, elevation, layout

- **Spacing:** 4 px base (Tailwind default scale). Rows 8×12 (compact) or 12×16 (default); panel padding 16; section gap 24–32.
- **Radius:** `xs` 4 (badges), `sm` 6 (buttons, inputs), `md` 8 (cards, menus), `lg` 12 (panels, dialogs, dropzone). Highlights 2. Deliberately tighter than consumer apps.
- **Elevation:** `0` flat inside panels; `1` cards; `2` popovers, toasts, sticky decision bar; `3` dialogs, command palette. In dark mode, step the surface (`surface → surface-2 → surface-3`) rather than relying on shadow.
- **Layout:** top bar 48 px + left nav 240 px (collapsible to 56). Review screen: document pane left (min 480, flexible) + findings pane right (400–480, resizable via a keyboard-operable separator). Below 1024 px the panes become tabs (Document | Findings). Tailwind default breakpoints.

## 6. Motion

| Token | Value | Use |
|---|---|---|
| `--duration-fast` | 120 ms | Hover, press, colour |
| `--duration-base` | 200 ms | Popovers, row insert, highlight pulse |
| `--duration-slow` | 320 ms | Panel open, report preview |
| `--ease-out` | `cubic-bezier(.2,.8,.2,1)` | Default |
| `--ease-in-out` | `cubic-bezier(.65,0,.35,1)` | Scroll-to-clause |

- **Streamed finding:** fades and expands in (200 ms, height 0 → auto + opacity), no slide.
- **Jump to clause:** smooth scroll, then the highlight outline pulses twice (2 × 600 ms).
- **Presence:** avatar or caret moves with a 120 ms ease, nothing more.
- **`prefers-reduced-motion`:** jump instead of smooth scroll; static 2 px outline for 2 s instead of pulse; no height animation or shimmer; streamed text renders in chunks, not tokens. Exposed as `--motion-ok: 0/1`.

## 7. Component inventory

**Common states** for every interactive component:

| State | Treatment |
|---|---|
| Hover | Tint at 5% of `--text` |
| Focus-visible | 2 px `--focus` ring, 2 px offset; never removed, never hidden under sticky bars (WCAG 2.4.11) |
| Active | 8% tint |
| Disabled | `surface-3` fill + `text-muted`, reason via tooltip or `aria-describedby`; never opacity-only |
| Loading | Spinner replaces the leading icon, label stays, `aria-busy` |
| Error | `critical` text + `WarningCircle` + message under the field |
| Read-only (Viewer role, offline) | Controls disabled with the reason ("Viewers can't make decisions", "Reconnecting, changes are paused") |

Icons: Phosphor regular; filled only for status. 16 px inline, 20 px in buttons.

| # | Component | Variants | States | Key rules |
|---|---|---|---|---|
| 7.1 | **Finding card** | `compact` (row: severity, title, control, state, band), `expanded` (all fields), `report` (read-only with final decision, decider, reason) | `streaming` (skeleton fields, "Writing…", decisions disabled "Finding still being written"), `complete-pending`, `accepted`, `rejected`, `edited`, `escalated` (assignee shown), `low-confidence` marker, `conflict`, `interrupted`, `selected` (accent left bar + `accent-subtle`) | Anatomy: 4 px severity edge bar + shape icon · badge · control ID (mono) · finding ID · decision state · title · verbatim quote (serif, 2-line clamp) + location (§ · page) · AI rationale (tinted, "AI" tag) · confidence meter · remediation (tinted, collapsible) · decision controls · comment count · viewers. **Do** keep the quote verbatim with location. **Don't** paraphrase in the quote slot or hide rationale in a tooltip |
| 7.2 | **Clause highlight** | single, overlapping (≤ 3 stacked underlines + count marker, e.g. `◆3`) | default, hover (1 px `border-strong` outline), active (2 px `--focus` + pulse), accepted (tint mixed 60% toward `surface`), rejected (no tint, dotted underline, hidden unless "Show rejected"), streaming (appears without scrolling the user) | `<mark>` over parsed text using `[charStart, charEnd)` (D-05); gutter marker with severity shape; hover/focus opens a mini-list ordered by severity; Enter selects first, Tab moves through list; reachable by Tab only in "Navigate highlights" mode (`[` / `]`); `aria-describedby` → "Critical finding F-0142, needs decision" |
| 7.3 | **Severity badge** | `solid` (critical/high), `subtle` (medium/low), `outline` (info), filter chip (`aria-pressed`) | default, pressed (chip), with count (`Critical · 3`) | 20 px pill, icon + label; label never dropped except icon-only in the gutter with `aria-label` |
| 7.4 | **Confidence meter** | 3-segment meter + band + reason | High, Medium, Low; uncalibrated | Never a percentage; tooltip "Based on [n] labelled examples, findings in this band were correct about [x]% of the time" only after calibration, else "Uncalibrated estimate". **Low:** dashed card border, "Needs careful review", rationale expanded, Accept enabled only after "Show in document" was used, **stays in its severity group** + "Low confidence" filter chip (D-01). Never green for high confidence; never hide low by default. `role="img"` + `aria-label` |
| 7.5 | **Presence avatars** | top-bar stack (≤ 4 × 24 px + `+N`), on-finding (16 px), in-document caret (stretch) | active, idle (> 2 min, 50% ring), editing ("Priya is editing…"), disconnected (removed after 30 s) | 6 identity hues avoiding severity hues (indigo, violet, teal, pink, slate, lime-olive); name on hover/focus; click opens list with name, **role** and current finding |
| 7.6 | **Live stream indicator** | header pill + thin progress bar | Connecting · Live/analyzing ("Live · Analyzing 34 / 61 clauses") · Live/idle ("Analysis complete · 18 findings") · Reconnecting (hollow amber dot, "changes are paused") · Offline (dashed critical dot, "read-only until reconnected", [Retry now]) · Failed (octagon, "Analysis stopped: … ", partial coverage noted) | Live regions: polite throttled for progress; assertive only for offline and failure |
| 7.7 | **Decision controls** | buttons Accept `A`, Reject `R`, Edit `E`, Escalate `X`; overflow (P2: "Mark as duplicate of…"); batch (P2) | default, submitting (optimistic "Saving…"), saved, failed (revert + [Retry]), disabled (streaming / offline / Viewer, with reason), conflict banner | Inline required reason (≥ 10 chars) with chips `Not applicable`, `Already covered by §…`, `Incorrect mapping`, `Duplicate`. Edit: title, severity (reason), rationale, remediation (D-12). Escalate: assignee picker + reason (D-04). Undo toast 8 s (`Z`), then "Change decision" with reason. Conflict: "Jamal rejected this 5 s ago: '…'" [Keep theirs]; [Override…] **Owner only**, reason required, logged (D-03) |
| 7.8 | **Comment thread** | flat list in expanded card | empty, sending, failed + [Retry], someone typing (debounced, polite) | Enter sends, Shift+Enter newline; decisions appear inline as system rows; no @mentions, reactions, nested threads or editing in MVP |
| 7.9 | **Audit log entry** | in-card (last 3), full log screen (filter by actor, action, finding; JSON export) | read-only only | Server timestamp to the second in viewer's zone (UTC on hover), actor (human or `AI agent` + model + pack version), uppercase action (incl. `OVERRIDE`, `ESCALATED`, `SIGNED OFF`), target, reason, before → after, event ID (mono). No edit or delete affordance anywhere |
| 7.10 | **Report preview** | A4 page preview + options rail | Generating, Draft (watermark; draft export allowed), Blocked ("12 findings still need a decision" + links; sign-off disabled), Ready to sign, Signed (locked; signer, time), Superseded (v1 after a change), Failed (+ retry) | One report per project with a section per framework (D-06). Sections: cover, summary (severity × decision per framework), findings (accepted/edited by severity → control), escalations (open), appendix (rejected + reasons), coverage (assessed / abstained / out of scope), evidence trail (audit digest, model IDs, prompt + pack versions), disclaimer (cover + every footer), sign-off block (attestation; hash is stretch, D-02). Export `.pdf` / `.json` with version + date in filename |
| 7.11 | **Navigation** | top bar, left nav, skip links, ⌘K (P2) | active item (accent bar + `surface-3`), collapsed | Top bar: product · project switcher · breadcrumb (Project › Document) · live indicator · presence · user menu. Left nav: Projects, Documents, Frameworks, Reports, Audit log, Settings. Skip links "Skip to findings" / "Skip to document" |
| 7.12 | **Upload dropzone** | multi-file | idle, drag-over ("Release to upload"), uploading (per-file progress, %, size, [Cancel]), processing (Uploaded → Parsing → Chunking → Indexing → Ready), rejected (inline, names the limit), parse failure (§8.2) | Caption "PDF (with text layer), DOCX, TXT · up to 10 MB / 50 pages"; real `<input type="file">`, drag never the only way; **data notice** above the zone (D-08) |
| 7.13 | **Data notice banner** | inline banner (upload, first run), compact footer line (review) | default; dismiss not allowed on upload screen | "Demo only: use synthetic or public sample contracts. Don't upload real confidential data." `info` styling with `Info` icon (D-08) |
| 7.14 | **Framework card / pack upload** | checkbox card per framework; Internal Policy YAML upload | selected, `Preview · Limited control coverage` badge (ISO 27001, HIPAA, Internal), YAML validating, YAML invalid (line-numbered errors), YAML loaded (pack name + version) | Each card: one-line description + pack version. YAML editor is Phase 2 (D-07) |
| 7.15 | **Toasts** | status | auto-dismiss 5 s (8 s for undo), pause on hover/focus | `role="status"`. Use for decision saved + Undo, export ready. Never for streamed findings, connection state or blocking errors (use inline banners) |
| 7.16 | **Empty and skeleton states** | no projects ("Create your first review"), no documents (dropzone), analysis running (skeleton), **no findings** ("No issues found for GDPR in this document" + [Confirm no findings] + coverage "61 clauses checked against 28 controls"), filters exclude all ([Clear filters]) | skeleton matches final layout; static under reduced motion | 40 px icon in tinted circle · title · one sentence · one primary action. Never a blank pane |
| 7.17 | **Reconnect summary chip** | in findings toolbar | shown after replay; dismissible | "While you were away: 2 decisions by Jamal, 3 new findings [Show]" |

## 8. Key screens and flows

### 8.1 First run (≤ 3 steps, skippable)
1. **Welcome:** "Review contracts against compliance frameworks, with every AI finding cited and decided by you." [Start a review] [Try with a sample contract]. The sample is preloaded so an interviewer reaches a live review in about 30 s (target). Data notice visible.
2. **Create project:** name; framework checkbox cards (GDPR and SOC 2 full; ISO/IEC 27001, HIPAA, Internal Policy with `Preview` badge); Internal Policy offers "Use sample pack" or "Upload YAML"; invite people with a role (Owner / Reviewer / Viewer), optional.
3. **Upload** (8.2), then land in Live review. A first-visit coach mark (dismissible, never repeated) points at the finding list, Show in document, decision keys and `?`.

### 8.2 Upload
```
┌ New review › Upload ────────────────────────────────────────────┐
│ ⓘ Demo only: use synthetic or public samples. Don't upload real │
│   confidential data.                                            │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │      ⇪  Drop a contract or policy, or [Browse files]       │   │
│ │      PDF (text layer), DOCX, TXT · up to 10 MB, 50 pages   │   │
│ └───────────────────────────────────────────────────────────┘   │
│ msa-acme-2026.pdf   2.4 MB  ███████░░░ 71%            [Cancel]  │
│ dpa-acme.docx       0.3 MB  ✓ Uploaded → ◌ Parsing             │
│ Frameworks: [GDPR ✓] [SOC 2 ✓] [ISO 27001] [HIPAA] [Internal]   │
│                              [Start review] (enabled when ≥1 ready)│
└─────────────────────────────────────────────────────────────────┘
```
Failure messages (each with a next step; failed rows offer [Replace] [Remove]; other files continue):
- Encrypted: "This PDF is password-protected. Remove the password and upload again."
- Scanned / image-only: "No selectable text found. Scanned PDFs aren't supported yet; upload a text PDF or DOCX." (OCR is Phase 2.)
- Over limit: "msa.pdf is 14 MB / 72 pages. The limit is 10 MB and 50 pages."
- Corrupt or unsupported: names the file and type.
- Partial parse (Phase 2; MVP parsing is pass/fail): "Parsed 38 of 41 pages. Pages 12–14 could not be read." [Continue anyway] [Replace file]; the report records the gap.

### 8.3 Live review (core screen)
```
┌ Acme MSA v3 · GDPR, SOC 2 ── ● Live · Analyzing 34/61 ── (P)(J)+1 ──────┐
├──────────── Document (parsed text, serif) ─┬─── Findings (18) ──────────────┤
│ ◆  7.2 The Supplier may process ▔▔▔▔       │ [Critical 2][High 4][Med 7][Low 5]│
│ ⬣3 Customer Data as reasonably             │ [Low confidence 3] Filter ▾ Sort: Sev│
│    required to perform the Services.       │ ▌⬣ Critical  F-0142  Art.28(3)(a) │
│                                            │ ┆⬣ Critical  F-0147  ◔ Needs careful review│
│ ●  7.3 Sub-processors shall be …           │ ▌▲ High  F-0139  CC6.1        ✓   │
│                                            │ ░░░░░░░░ writing… (streaming)     │
│                                            │ ── 3 new findings ↓ (click/N) ──  │
├────────────────────────────────────────────┴───────────────────────────────┤
│ Selected F-0142 · [Accept A] [Reject R] [Edit E] [Escalate X] · 12 need decision │
└──────────────────────────────────────────────────────────────────────────────┘
```
- **Grouping and sort:** by severity, then confidence within the group; low-confidence findings stay in their severity group with the dashed marker; a "Low confidence" chip filters them (D-01).
- **Streaming:** findings insert in sort position. If the user has scrolled away or has a selection, the list does not move; a "N new findings" pill appears (`N`). Row height is reserved when a finding starts. If the token-streaming flag is off, findings arrive whole and the `streaming` state is skipped (D-10).
- **Document pane** is parsed text with highlights (D-05); a multi-document project shows a document switcher in the breadcrumb.
- **Selection** syncs both panes. The sticky decision bar never covers the focused element (`scroll-padding`).
- **Roles:** Viewers see the same screen with decision controls disabled and a reason.
- **Keyboard map** (`?`; single-key shortcuts can be disabled or remapped, inactive in text fields):

| Key | Action |
|---|---|
| `J` / `K` (↓ / ↑ in list) | Next / previous finding |
| `G` / `Enter` | Go to cited clause / open finding |
| `[` / `]` | Previous / next highlight |
| `A` `R` `E` `X` | Accept / Reject / Edit / Escalate |
| `C` | Comment |
| `Z` | Undo last decision (8 s) |
| `N` | Jump to new findings |
| `F` | Focus filters |
| `Esc` | Close popover / return focus |
| `?` | Shortcut help |

### 8.4 Reconnecting / offline
- **Detection:** socket close or no heartbeat for 30 s (2 × 15 s) → `Reconnecting`; backoff with jitter 1 s → 30 s cap. After 60 s or `navigator.onLine = false` → `Offline`.
- **Read-only** (D-09): decision buttons disabled with "Reconnecting, changes are paused"; comment and reason drafts kept locally; reading, filtering and navigating still work.
- **In-flight stream:** a partial finding is marked `Interrupted`, keeps its text greyed, shows "Resuming…". After replay it is replaced in place by the persisted finding (dedupe by `seq`), or removed with "1 interrupted finding was discarded by the analyzer".
- **Unacknowledged decisions:** show `Saving…`; on reconnect the client checks server state: "Saved" or "Not saved: [Submit again]". Never silently resubmitted.
- **Replay:** client sends its last event id (`lastSeq`); others' changes apply from replay and the summary chip (7.17) appears. If the gap exceeds the replay window: "Reloading the latest state…" with a full-list skeleton.
- **Presence** is cleared on disconnect and rebuilt on reconnect.
- **Announcements:** "Connection lost. Changes paused." (assertive, once); "Reconnected. 5 updates applied." (polite).

### 8.5 Report (preview, export, sign-off)
1. **Report** tab → completeness check ("All 18 findings decided ✓ · 1 escalation open ⚠"), per framework.
2. **Preview** (7.10) with options: frameworks included, rejected appendix y/n, comments y/n. Draft PDF/JSON export always available, watermarked "DRAFT".
3. **Sign-off (Owner only):** checkbox "I have reviewed these findings and approve this report" + name (pre-filled, read-only) + [Sign off]. Recorded in the audit log and the report; locks the version (D-02). Hash, re-auth and e-signature are stretch.
4. **After signing:** export final PDF/JSON. Any later decision change creates v2; v1 stays viewable, marked "Superseded".

### 8.6 System states
| State | Treatment |
|---|---|
| Empty | 7.16. Never a blank pane |
| Initial load | Skeleton for both panes; document text first, findings after; error after 15 s |
| Analysis error | Indicator `Failed`; completed findings stay usable; banner names where it stopped; report notes partial coverage. Resume-from-failure button is Phase 2 |
| API error | Inline on the element + [Retry]; no toast for blocking errors |
| Reconnecting / offline | 8.4 |

## 9. Accessibility

Target **WCAG 2.2 AA**. Each item maps to an acceptance criterion in [`ACCEPTANCE-CRITERIA.md`](ACCEPTANCE-CRITERIA.md) §11.

| Area | Rule |
|---|---|
| Keyboard | Full flow (create, upload, review, decide with reasons, comment, preview, export, sign off) by keyboard only; no traps; focus ring always visible and not obscured (2.4.11) |
| Live regions | Polite batched summary at most every 5 s ("3 new findings: 1 critical, 2 medium"); never per token; criticals batched, not interrupting; assertive only for connection loss and analysis failure; user can mute stream announcements |
| Focus management | Popovers and inline editors take focus and return it to the trigger; after a decision focus advances to the next "Needs decision" (setting: stay/advance) and announces it |
| Reflow | 200% zoom and 320 px-equivalent width: no two-dimensional scrolling (document text excepted); split view becomes tabs |
| Reduced motion | No smooth scroll, pulse, shimmer or height animation; streamed text in chunks |
| Colour independence | Grayscale: severity and decision state identifiable by label + icon + underline style; overlapping highlights distinguishable |
| Contrast | Only §4.3 pairs; axe reports 0 contrast violations on review, upload and report screens in both themes |
| Targets and shortcuts | Targets ≥ 24 × 24 px (2.5.8); single-key shortcuts can be turned off or remapped (2.1.4) and are inactive while typing |
| Screen reader semantics | Findings list is a `listbox` or `list` with roving focus; accessible name includes severity, title, control and decision state; highlights use `aria-describedby`; confidence meter has a text equivalent; progress uses `role="progressbar"` with text value; resizable split uses `role="separator"` |
| Redundant entry (3.3.7) | Reason and comment text survives validation errors, reconnects and switching findings |
| Disabled states | Always state why (streaming, offline, role) |
