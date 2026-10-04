# Compliance Review Copilot: design input

From: Design Head · For: Chief of Staff (PRD, design system, acceptance criteria) · Oct 5, 2026 IST
Scope: MVP for a 2-3 week portfolio build. Next.js 16 + React 19 + Tailwind 4. No screens or Figma exist yet; this document is the spec.
Companion files in this folder: `design-contrast.py` (contrast check, run `python3 design-contrast.py`) and `design-contrast.json` (computed values).
Aligned with `input/engineering.md` (read Oct 5): file limits, citation validation, the WebSocket replay model, MVP scope, and cut order. The remaining differences are listed in §6.

---

## 1. Design principles

1. **Evidence before conclusions.** A finding is shown as *clause → control → why → severity*, in that order. The exact cited text is always one click (or one key) away, and is highlighted in the document. Engineering validates citations as exact substrings and drops findings that fail, so every finding shown has a resolvable clause. The analysis summary shows the drop count ("2 findings discarded: citation check failed") for transparency.
2. **AI output is attributable and reversible.** Everything the AI wrote carries an AI marker, plus the model, framework pack version, and timestamp in the audit log. Human edits show a diff against the AI original. Every decision can be undone (or superseded, with a reason), and nothing is ever deleted from the trail.
3. **The human decision is final.** The AI proposes; reviewers decide. There is no auto-accept, even at high confidence. The report only includes findings with a human decision, and sign-off is a named person's action.
4. **Show honest confidence.** Confidence is shown as a band (High / Medium / Low) with the reason, not as a precise-looking percentage. Low confidence is made louder, not hidden.
5. **The audit trail is visible.** Who did what, when, and why is always visible in context (on the finding) and as a project log. Reasons are required for reject, escalate, and override.
6. **Calm density, live without noise.** Reviewers scan dozens of findings, so rows are compact, the palette is neutral, and color is reserved for severity and state. Streaming and presence are subtle: no auto-scroll, no jumping focus, and no toasts for every new finding.
7. **Never color alone.** Every severity and status uses text label + icon + shape, and color is only the fourth cue.

---

## 2. Design tokens

### 2.1 Color rules
- Neutral slate base (hue 255) and **one accent: indigo (hue 272)**, used for actions, selection, and focus. Indigo was chosen because it doesn't collide with any severity hue.
- **Severity:** critical (red 25), high (orange 45-50), medium (amber 75-92), low (cyan 220), info (neutral).
- **Decision state:** success (green 150) for accepted/resolved; pending (neutral) for "awaiting decision".
- `info` and `pending` intentionally share the neutral color. They never appear in the same slot, and they differ by icon and shape.
- **AI tint:** a faint violet background (`--ai-tint`) marks AI-authored text blocks (summary, remediation). Human-edited text drops the tint.
- **Severity variants:**
  - `-subtle` is the badge or row background.
  - `-hl` is the in-document highlight; it is stronger, and text on it still passes 4.5:1.
  - `-solid` is used only for critical and high badges, to add weight.
- `--border` is decorative. Input outlines, checkboxes, and toggles use `--border-strong` (≥3:1, WCAG 1.4.11).
- Hex values are fallbacks; OKLCH values are upgraded via `@supports`. Values are gamut-fitted to sRGB, so both render the same color.

### 2.2 Severity encoding (color is never the only cue)

| Severity | Label (always shown) | Icon / shape (Phosphor) | Badge style | Doc highlight | Sort |
|---|---|---|---|---|---|
| Critical | `Critical` | Octagon + `!` (`WarningOctagon`) | **Solid** fill, `critical-on-solid` text | `critical-hl` + 3px solid underline | 1 |
| High | `High` | Triangle (`Warning`) | **Solid** fill | `high-hl` + 2px solid underline | 2 |
| Medium | `Medium` | Diamond (`Diamond`) | Subtle fill + 1px border | `medium-hl` + 2px dashed underline | 3 |
| Low | `Low` | Circle (`Circle`) | Subtle fill | `low-hl` + 1px dotted underline | 4 |
| Info | `Info` | Square-i (`Info`) | Neutral outline | no tint, dotted underline | 5 |

| Decision state | Label | Icon |
|---|---|---|
| Pending | `Needs decision` | Hollow dashed circle |
| Accepted | `Accepted` | `CheckCircle` (filled) |
| Rejected | `Rejected` | `XCircle`, title struck through |
| Edited | `Accepted · edited` | `PencilSimple` dot |
| Escalated | `Escalated to <name>` | `ArrowFatLineUp` |

The underline styles (solid/dashed/dotted) keep severity distinguishable in grayscale and for color-blind users. Grayscale review of the document pane is an acceptance criterion (§5).

### 2.3 Token values

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

### 2.4 Contrast results (computed)
Method: the same as the tubecp check. OKLCH → linear sRGB → gamut-fit (reduce chroma) → 8-bit sRGB → WCAG 2.x relative luminance. Text needs 4.5:1. Non-text (focus ring, control borders, solid badges against the surface, underline marker against its own highlight) needs 3:1.
**Result: 136 / 136 checks pass (68 pairs × light and dark).** Lowest text pair: light `text-muted` on `surface-3` at 5.00:1. Lowest non-text pair: light `border-strong` on `bg` at 3.47:1.

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

Pairs not in this table are not approved. For example: severity text on another severity's highlight, `text-muted` on `-hl`, or any text on `-solid` other than its `-on-solid`. When **highlights overlap**, the tint used is the highest severity's `-hl`, never a blended mix (blends are not contrast-checked).

### 2.5 Typography
| Role | Font | Notes |
|---|---|---|
| UI | **Inter** (variable, OFL, Google Fonts) | `font-feature-settings: "tnum"` for counts and times |
| Document pane | **Source Serif 4** (variable, OFL) | The document reads as a document, visually separate from the AI and UI chrome |
| IDs, clause refs, control IDs, hashes | **JetBrains Mono** (OFL) | `GDPR Art. 28(3)(a)`, `SOC2 CC6.1`, `F-0142` |

| Token | Size / line-height | Weight | Use |
|---|---|---|---|
| `text-caption` | 12 / 16 | 400-500 | Timestamps, meta, legal. Minimum size |
| `text-label` | 13 / 18 | 500 | Badges, labels, tabs |
| `text-body-sm` | 14 / 20 | 400 | Finding rows, comments, log |
| `text-body` | 15 / 24 | 400 | Finding detail, report body |
| `text-doc` | 16 / 28 (serif) | 400 | Document pane, max 72ch |
| `text-title-sm` | 16 / 24 | 600 | Card/panel titles |
| `text-title` | 20 / 28 | 600 | Screen titles |
| `text-headline` | 28 / 36 | 600 | Onboarding, report cover |

Rules: sentence case, no text below 12px, uppercase only for ≤2-word overlines with +0.04em tracking.

### 2.6 Spacing, radius, elevation, layout
- **Spacing:** 4px base (Tailwind default scale). Row padding is 8×12 (compact) or 12×16 (default); panel padding is 16; section gap is 24-32.
- **Radius:** `xs` 4 (badges), `sm` 6 (buttons, inputs), `md` 8 (cards, menus), `lg` 12 (panels, dialogs, dropzone). Highlights are 2px. These are deliberately tighter than consumer apps, for an enterprise feel.
- **Elevation:**
  - `0`: flat, inside panels.
  - `1`: cards, `0 1px 2px` at 6%.
  - `2`: popovers, toasts, the sticky decision bar.
  - `3`: dialogs and the command palette.
  - In dark mode, raise the surface step (`surface → surface-2 → surface-3`) instead of relying on shadow.
- **Layout:**
  - App shell: top bar 48px + left nav 240px (collapsible to 56px).
  - Review screen: a split view with the document pane on the left (min 480, flexible) and the findings pane on the right (400-480, resizable). Below 1024px, the panes become tabs (Document | Findings).
  - Breakpoints: Tailwind defaults.

### 2.7 Motion
| Token | Value | Use |
|---|---|---|
| `--duration-fast` | 120ms | hover, press, color |
| `--duration-base` | 200ms | popovers, row insert, highlight pulse |
| `--duration-slow` | 320ms | panel open, report preview |
| `--ease-out` | `cubic-bezier(.2,.8,.2,1)` | default |
| `--ease-in-out` | `cubic-bezier(.65,0,.35,1)` | scroll-to-clause |

- **New streamed finding:** fades and expands in at 200ms (height 0 → auto, opacity), with no slide.
- **Jump to clause:** smooth-scrolls, then the highlight pulses its outline twice (2 × 600ms).
- **Presence cursors:** move with a 120ms ease and nothing more.
- **`prefers-reduced-motion`:** no smooth scroll (jump instead), no pulse (a static 2px outline for 2s instead), no height animation, and streaming text renders in chunks instead of token by token. Exposed as `--motion-ok: 0/1`.

### 2.8 Tailwind 4 `@theme` block

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
Fonts are loaded with `next/font/google` (`Inter`, `Source_Serif_4`, `JetBrains_Mono`) using `variable: "--font-inter" | "--font-source-serif" | "--font-jetbrains"`. Don't name a `next/font` variable `--font-sans`; that creates a self-reference inside `@theme`. This block compiles on Tailwind 4.3.3.

---

## 3. Component inventory

Common states for all interactive components:
- **Hover:** row/control tint, 5% of `--text`.
- **Focus-visible:** 2px `--focus` ring with 2px offset. It is never removed, and it is never hidden under sticky bars (WCAG 2.4.11).
- **Active:** 8% tint.
- **Disabled:** `surface-3` fill + `text-muted` text, with the reason in a tooltip or `aria-describedby`. Never opacity-only.
- **Loading:** spinner replaces the leading icon, the label stays, and `aria-busy` is set.
- **Error:** `critical` text + `WarningCircle` + message under the field.

Icons: **Phosphor**, regular weight; fill only for status. 16px inline, 20px in buttons. Use the same icon library as Bharath's other app.

### 3.1 Finding card
```
┌─▌───────────────────────────────────────────────────────────────┐
│ ▌ ⬣ Critical   GDPR Art. 28(3)(a)   F-0142        ◔ Needs decision│
│ ▌ Processor may act without documented instructions        (title)│
│ ▌ "The Supplier may process Customer Data as reasonably required…"│
│ ▌   §7.2 · p.4  [Show in document ↵]                    (citation)│
│ ▌ ┊AI┊ Why: Art. 28(3)(a) requires processing only on documented  │
│ ▌ ┊  ┊ instructions; §7.2 grants open discretion.                 │
│ ▌ Confidence ▮▮▯ Medium · "clause wording is ambiguous"           │
│ ▌ ┊AI┊ Suggested fix: Replace "as reasonably required" with …     │
│ ▌ [Accept A] [Reject R] [Edit E] [Escalate X]   💬 2   (●P)(●J)    │
└─────────────────────────────────────────────────────────────────┘
```
- **Anatomy:** severity edge bar (4px, severity color, with a matching shape icon) · severity badge · control ID (mono) · finding ID · decision state · title · quoted clause (serif, 2-line clamp) + location · AI rationale (AI tint + "AI" tag) · confidence meter · remediation (AI tint, collapsible) · decision controls · comment count · presence of people viewing it.
- **Variants:**
  - `compact` (list row): severity, title, control, state, confidence band.
  - `expanded` (selected): everything.
  - `report` (read-only, final decision + decider + reason).
- **States:**
  - `streaming`: fields fill in as tokens arrive, with skeleton bars for fields not yet received and a "Writing…" caption. Decision controls are disabled with the reason "Finding still being written".
  - `complete-pending`, `accepted`, `rejected` (dimmed to `text-secondary`, title struck, still listed under the "Rejected" filter), `edited`, `escalated`.
  - `low-confidence` (see 3.4).
  - `conflict`: someone else decided while you were editing.
  - `interrupted`: the stream dropped before the finding was complete.
- **Selected:** accent left bar + `accent-subtle` bg, and the linked clause gets an active highlight.
- **Do:** keep the quote verbatim and always show the location.
- **Don't:** paraphrase the clause in the quote slot, or hide the rationale behind a tooltip.

### 3.2 Clause highlight (in-document)
- **Rendering:** a `<mark>` span over the parsed text, using the `-hl` tint of the highest severity among the findings linked to it, plus that severity's underline style. In the left margin there is a gutter marker (severity shape icon) at the line.
- **Overlap:**
  - Up to 3 underlines stack (2px apart, each with its own severity style), and the margin marker shows a count, e.g. `◆3`.
  - Hovering or focusing the mark opens a mini-list popover: "3 findings: Critical F-0142, Medium F-0150, Low F-0151".
  - Enter on the mark selects the first finding; Tab moves through the list.
  - For more than 3 overlapping findings, show the 3 highest underlines plus the count.
- **States:**
  - Default.
  - Hover (outline 1px `--border-strong`).
  - Active, linked to the selected finding (2px `--focus` outline + pulse).
  - Decided: accepted findings keep the tint at 60% mixed toward `surface` (this always moves away from the text color, so contrast only rises above the checked `-hl` value); rejected findings lose the tint and keep a dotted underline. Both are toggleable via "Show rejected".
  - Streaming: when a new finding's citation arrives, its highlight appears without scrolling the user away.
- **Linking:** finding → clause (Show in document / `G`) and clause → finding (click or Enter). Both directions keep context, and `Esc` returns focus to where you came from.
- **Accessibility:** each mark has `aria-describedby` pointing to a visually hidden "Critical finding F-0142, needs decision". Marks are reachable by Tab only when the "Navigate highlights" mode is on (`[` / `]` keys); otherwise Tab would trap users in long documents.
- Citations are guaranteed exact substrings with char offsets (engineering AC-6), so highlights map directly to `[charStart, charEnd)`.

### 3.3 Severity badge
- 20px pill: icon + label (+ optional count `Critical · 3`).
- Variants: `solid` (critical/high), `subtle` (medium/low), `outline` (info). The label is never dropped, even in compact rows. The icon-only form is allowed in the margin gutter, and only with `aria-label`.
- A **filter chip** variant appears in the findings toolbar, as a toggle button with `aria-pressed`.

### 3.4 Confidence meter (honest AI confidence)
- **Display:** a 3-segment meter + band label (`High` / `Medium` / `Low`) + a one-line reason from the agent ("clause wording is ambiguous", "control mapping inferred from similar clause"). Never show "97.3%".
- **Source of the band:** thresholds on the model's score, calibrated against the evaluation harness. The tooltip says: "Based on [n] labeled examples, findings in this band were correct about [x]% of the time." It shows only once the eval exists. If not yet calibrated, the tooltip says "Uncalibrated estimate".
- **Low-confidence treatment:**
  - Dashed card border.
  - "Needs careful review" label.
  - Rationale expanded by default.
  - Accept requires opening the cited clause first (the "Show in document" action must have been used).
  - Sort: engineering AC-7 sorts "Needs review" after confident findings. Design prefers keeping these findings within their severity group, so that a low-confidence critical isn't buried below confident lows. Open question §6.
- **Never:** green for "high confidence" (confidence is not correctness), auto-accept, or hiding low-confidence findings by default.
- **Accessibility:** `role="img"` and `aria-label="Confidence: Medium. Clause wording is ambiguous."`.

### 3.5 Presence avatars (multiplayer)
- **Top bar:** a stack of up to 4 avatars (24px, initials on neutral, plus a 2px ring in a per-user identity color), then `+3`. Clicking opens a list with each person's name, role, and what they are viewing ("on F-0142").
- **On a finding:** 16px avatars of people currently viewing or editing it. If someone is editing: "Priya is editing…" (caption) and an outlined pencil.
- **In the document:** a thin colored caret or label at another person's selected clause (optional; it can be cut from the MVP).
- **Identity colors** come from a fixed set of 6 hues that avoid the severity hues (indigo, violet, teal, pink, slate, lime-olive). The name text is always shown on hover or focus, so color is never the only cue.
- **States:** active, idle (>2 min, 50% ring, "idle" in the tooltip), disconnected (removed after 30s).

### 3.6 Live stream indicator
- In the review header: `● Live · Analyzing 34 / 61 clauses · GDPR, SOC 2` + a thin progress bar + [Pause stream] (optional).
- **States:**

| State | Visual | Text | Live region |
|---|---|---|---|
| Connecting | spinner | "Connecting…" | none |
| Live / analyzing | pulsing dot (static under reduced motion), accent | "Live · Analyzing 34 / 61 clauses" | polite, throttled (see 5.4) |
| Live / idle | solid dot, success | "Live · Analysis complete · 18 findings" | polite, once |
| Reconnecting | hollow dot, medium (amber) | "Reconnecting… (attempt 2) · changes are paused" | polite |
| Offline | dashed hollow dot, critical | "Offline · read-only until reconnected" [Retry now] | assertive, once |
| Failed | octagon, critical | "Analysis stopped: model timeout on clause 35" [Resume] | assertive |

### 3.7 Decision controls
- **Buttons:**
  - Accept (`A`).
  - Reject (`R`): a reason is required.
  - Edit (`E`): opens inline editing of title, severity, control mapping, and remediation. You can edit severity, but changing it requires a reason. The result is saved as "Accepted · edited".
  - Escalate (`X`): pick an assignee + a reason is required.
  - The overflow menu has "Mark as duplicate of…".
- **Required reason:** inline, not a modal. A textarea expands under the buttons, with quick-pick chips (`Not applicable`, `Already covered by §…`, `Incorrect mapping`, `Duplicate`) + free text, min 10 chars. Submitting is disabled until valid, with the reason stated.
- **Undo:**
  - A toast "Accepted F-0142 · Undo (Z)" stays for 8s.
  - After that, undo is a "Change decision" action that requires a reason.
  - Both paths add audit entries; nothing is erased.
- **States:**
  - Default.
  - Submitting: optimistic, with the card showing "Saving…".
  - Saved: the decision state updates for everyone.
  - Failed: the card reverts, with an inline error and [Retry].
  - Disabled while streaming, while offline, or when you lack permission. A reason is always given.
  - **Conflict:** if someone else decided first, show a banner on the card: "Jamal rejected this 5s ago: 'Already covered by §9.' [Keep theirs] [Override…]". Override requires a reason.
- **Batch actions:** select multiple via checkboxes or Shift+J/K, then Accept or Reject with one shared reason. MVP: Accept only for selected low/info findings; flag this as optional.

### 3.8 Comment thread
- On the finding (expanded view): a flat chronological list (avatar, name, time, text; @mentions are out of the MVP per engineering), with a composer at the bottom (Enter sends, Shift+Enter adds a newline). Decision events appear inline as system rows ("Priya accepted · reason…").
- **States:** empty ("No comments yet"), sending (gray "Sending…"), failed ([Retry]), edited ("edited" label, with the history in the audit log), someone typing ("Jamal is typing…", polite, debounced).
- MVP: no reactions and no threads within threads.

### 3.9 Audit log entry
```
10:42:13 IST  ●P Priya Shah   REJECTED  F-0142  GDPR Art. 28(3)(a)
              Reason: "Already covered by DPA Annex 2 §1."
              Previous: Pending (AI · <model id> via Bedrock · pack GDPR v0.3)
              [View finding]  [Copy event ID evt_7f3…]
```
- **Fields:** server timestamp (to the second, in the viewer's timezone + UTC on hover), actor (human, or `AI agent` with a robot icon, model + pack version), action verb (uppercase label), target (finding ID, control), reason, before → after (diff for edits), event ID (mono).
- **Variants:** in-card history (last 3 entries) and the full log screen (filter by actor, action, or finding; export JSON).
- Entries are read-only. There are no edit or delete affordances anywhere.

### 3.10 Report preview
- A paper-style page preview (A4 ratio, serif body) in the main pane. The right rail has options (frameworks included, include rejected findings appendix y/n, include comments y/n), a completeness check, and export.
- **Sections:** cover (document, frameworks, date, reviewers), summary (counts by severity × decision), findings (accepted/edited, grouped by severity → control), escalations (open), appendix (rejected, with reasons), evidence trail (audit log digest, model IDs and prompt versions), sign-off block (attestation; document hash is a stretch goal).
- **States:**
  - Draft: a "DRAFT" watermark, and export as draft is allowed.
  - Blocked: "12 findings still need a decision" with [Review them] links, and sign-off disabled.
  - Ready to sign.
  - Signed: locked, with the signer, time, and hash. Any later change creates v2 and voids the signature on v1, with a visible note.
  - Generating: progress.
  - Failed: error + retry.
- **Export:** PDF and JSON buttons (`.pdf`, `.json`), with file names including the version and date.

### 3.11 Navigation
- **Top bar (48px):** product name · project switcher · breadcrumb (Project › Document) · live indicator · presence · ⌘K · user menu.
- **Left nav (collapsible):** Projects, Documents, Frameworks, Reports, Audit log, Settings. The active item gets an accent bar + `surface-3`.
- **⌘K command palette** (optional for the MVP): jump to a finding by ID, change filter, open a report.
- **Skip link:** "Skip to findings" / "Skip to document".

### 3.12 Upload dropzone
- A dashed `border-strong` box (12px radius), with an icon, "Drop a contract or policy here, or [Browse files]", and accepted types + limits in a caption: "PDF (with text layer), DOCX, TXT · up to 10 MB / 50 pages" (from engineering scope).
- **States:**
  - Idle.
  - Drag-over: accent border + `accent-subtle` bg + "Release to upload".
  - Uploading: a per-file row with a progress bar, % and size, and [Cancel].
  - Processing: the steps Uploaded → Parsing → Chunking → Indexing → Ready, each with a check.
  - Rejected type or size: an inline critical message naming the limit.
  - Parsing failure (see 4.2).
- Keyboard: the Browse button is a real `<input type="file">` label. Drag is never the only way.

### 3.13 Toasts
- Bottom-right, `surface` + elev-2, icon + one line + optional action. Auto-dismiss after 5s (8s for undo), pausing on hover or focus.
- `role="status"`; errors that block work use an inline banner instead of a toast.
- **Use for:** decision saved + Undo, export ready.
- **Don't use for:** each new streamed finding (that's the live region's job), or connection state (the live indicator handles it).

### 3.14 Empty and skeleton states
- **Empty:**
  - 40px icon in a tinted circle · title · one sentence · one primary action.
  - Variants:
    - No projects: "Create your first review".
    - No documents: show the dropzone.
    - No findings yet: "Analysis running" (skeleton).
    - No findings at all: "No issues found for GDPR in this document." This is still a decision point, with a [Confirm no findings] sign-off and the coverage stats: "61 clauses checked against 28 controls".
    - Filters exclude everything: [Clear filters].
- **Skeletons:** match the final layout (finding row: badge stub, 2 title lines, meter stub). Static `surface-2` blocks under reduced motion, with `aria-busy` on the container.

---

## 4. Key screens and flows

### 4.1 First run / onboarding (≤3 steps, skippable)
1. **Welcome:** "Review contracts against compliance frameworks, with every AI finding cited and decided by you." [Start a review] [Try with a sample contract]. The sample is preloaded, so an interviewer gets a demo in 30s.
2. **Create a project:** name + select frameworks (checkbox cards for GDPR, SOC 2, ISO/IEC 27001, HIPAA, Internal Policy, each with a one-line description + pack version. Per engineering, the MVP ships GDPR and SOC 2 in depth and the rest as stub packs, so those cards carry a `Preview` badge and the line "Limited control coverage") + invite reviewers (email, optional).
3. **Upload** (4.2). Then land in Live review.

A first-visit coach mark on the review screen (dismissible, never repeated) points at: the finding list, Show in document, decision keys, and `?` for shortcuts.

### 4.2 Upload
```
┌ New review › Upload ────────────────────────────────────────────┐
│ ┌───────────────────────────────────────────────────────────┐   │
│ │      ⇪  Drop a contract or policy, or [Browse files]       │   │
│ │      PDF (text layer), DOCX, TXT · up to 10 MB, 50 pages   │   │
│ └───────────────────────────────────────────────────────────┘   │
│ msa-acme-2026.pdf   2.4 MB  ███████░░░ 71%            [Cancel]  │
│ dpa-acme.docx       0.3 MB  ✓ Uploaded → ◌ Parsing             │
│ Frameworks: [GDPR ✓] [SOC 2 ✓] [ISO 27001] [HIPAA] [Internal]   │
│                                   [Start review] (enabled when ≥1 ready)│
└─────────────────────────────────────────────────────────────────┘
```
**Parsing failure states** (each with a plain message + next step):
- Encrypted or password-protected: "This PDF is password-protected. Remove the password and upload again."
- Scanned or image-only (no text layer): "No selectable text found. Scanned PDFs aren't supported yet; upload a text PDF or DOCX." (OCR is Phase 2 in engineering.)
- Over the limit: "msa.pdf is 14 MB / 72 pages. The limit is 10 MB and 50 pages."
- Corrupt or unsupported: name the file and the type.
- Partial parse (only if engineering supports partial parses; today it is pass/fail): "Parsed 38 of 41 pages. Pages 12-14 could not be read." [Continue anyway] [Replace file]. The report later states the gap.
- Each failed file row offers [Replace] and [Remove]; other files continue.

### 4.3 Live review (core screen)
```
┌ Acme MSA v3 · GDPR, SOC 2 ── ● Live · Analyzing 34/61 ── (P)(J)+1 ── ⌘K ┐
├──────────── Document (serif) ─────────┬─── Findings (18) ─────────────────┤
│ ◆  7.2 The Supplier may process ▔▔▔▔ │ [Critical 2][High 4][Med 7][Low 5]│
│ ⬣3 Customer Data as reasonably       │ Filter: Needs decision ▾ Sort: Sev│
│    required to perform the Services. │ ▌⬣ Critical  F-0142  Art.28(3)(a) │
│                                      │ ▌  Processor may act without…  ◔  │
│ ●  7.3 Sub-processors shall be …     │ ▌▲ High  F-0139  CC6.1        ✓   │
│                                      │ ▌  Access reviews not specified…  │
│                                      │ ░░░░░░░░ writing… (streaming)     │
│                                      │ ── 3 new findings ↓ (click/N) ──  │
├──────────────────────────────────────┴───────────────────────────────────┤
│ Selected F-0142 · [Accept A] [Reject R] [Edit E] [Escalate X] · 12 need decision │
└──────────────────────────────────────────────────────────────────────────┘
```
- **Streaming:** new findings insert in sort position. If the user is scrolled away or has a finding selected, the list **does not move**. A "N new findings" pill appears instead; clicking it or pressing `N` jumps to them. Row heights are reserved when a finding starts, to prevent layout shift.
- **Selection** syncs both panes. The decision bar is sticky at the bottom and never covers the focused element (scroll-padding).
- **Keyboard map** (shown with `?`; single-key shortcuts can be turned off or remapped in settings, per WCAG 2.1.4):

| Key | Action |
|---|---|
| `J` / `K` (or ↓ / ↑ in list) | Next / previous finding |
| `G` / `Enter` | Go to cited clause / open finding |
| `[` / `]` | Previous / next highlight in document |
| `A` `R` `E` `X` | Accept / Reject / Edit / Escalate |
| `C` | Comment |
| `Z` | Undo last decision (within 8s) |
| `N` | Jump to new findings |
| `F` | Focus filters |
| `Esc` | Close popover / return focus to finding list |
| `?` | Shortcut help |

- **Pane split:** resizable with a keyboard-operable separator (`role="separator"`, arrow keys).

### 4.4 Report (preview, export, sign-off)
1. Report tab → completeness check ("All 18 findings decided ✓ · 1 escalation open ⚠").
2. Preview (3.10). Options rail. Export Draft (PDF/JSON) is always available, watermarked.
3. **Sign-off:** "I have reviewed these findings and approve this report" checkbox + name (pre-filled, read-only) + [Sign off]. This is an attestation recorded in the audit log and the report, which locks v1. Engineering lists signed or tamper-evident reports as out of the MVP, so the SHA-256 hash, re-auth, and e-signature are stretch goals.
4. After signing: export the final PDF/JSON, and "Changes after sign-off create v2".

### 4.5 System states

| State | Treatment |
|---|---|
| **Empty** | See 3.14. Never a blank pane |
| **Loading** (initial project load) | Skeleton for both panes. Document text renders first, findings after. Timeout after 15s → error |
| **Error: analysis** (agent/LLM failure) | The live indicator shows `Failed`. Completed findings stay usable. Banner: "Analysis stopped at clause 35 of 61 (model timeout). [Resume from clause 35]". The report notes partial coverage until resumed |
| **Error: API** (save failed) | Inline on the affected element + [Retry]. Toasts are not used for blocking errors |
| **Reconnecting** | See below |
| **Offline** | See below |

**Reconnect and offline behavior** (pairs with the brief's "reconnect/resume with event replay"):
- **Detection** (engineering: heartbeat 15s, dead after 30s, backoff with jitter 1s → 30s cap): socket close or a dead heartbeat → `Reconnecting`. After 60s, or when `navigator.onLine=false` → `Offline`. Gap beyond the replay window → `resync.required`: "Reloading the latest state…" with a full-list skeleton, then a summary chip.
- **In-flight streamed findings:** a partially streamed finding is marked `Interrupted`, keeps its received text greyed, and shows "Resuming…". On reconnect the client sends `client.hello{lastSeq}` and the server replays persisted events. Token deltas are ephemeral and not replayed, so the draft row is **replaced in place** by the `finding.created` event for the same finding, with no duplicate row (dedupe by `seq`). If no `finding.created` arrives by `replay.end` and analysis is complete, the draft is removed with the note "1 interrupted finding was discarded by the analyzer".
- **Decisions during disconnect (MVP rule: read-only):**
  - Decision buttons are disabled with "Reconnecting, changes are paused".
  - Reason text and comment drafts stay in the textarea and are kept locally.
  - Decisions submitted but not acknowledged before the drop show `Saving…` → on reconnect, the client checks the server state for that finding. If the decision is committed, mark it saved. If it is not, show "Not saved: [Submit again]". It is never silently resubmitted.
  - (A stretch goal is an offline outbox with server-timestamped commits on reconnect. That is not in the MVP, because audit time must be server time.)
- **Others' changes during the gap** are applied from replay, and a summary chip appears: "While you were away: 2 decisions by Jamal, 3 new findings [Show]".
- **Presence** is cleared on disconnect and rebuilt on reconnect.
- **Announcements:** "Connection lost. Changes paused." (assertive, once), "Reconnected. 5 updates applied." (polite).

---

## 5. UX acceptance criteria

### 5.1 Trust and decisions
- **AC-1:** Given a finding is displayed, then it shows severity label + icon, control ID, verbatim quote, location, rationale, confidence band + reason, and an AI marker on AI-authored text.
- **AC-2:** Given I click "Show in document" or press `G`, then the document scrolls to the clause, the highlight is in the active state, and `Esc` returns focus to the same finding row.
- **AC-3:** Given I click a highlight linked to 2+ findings, then a list of those findings appears, ordered by severity, and each is selectable by keyboard.
- **AC-4:** Given I choose Reject or Escalate, when the reason is under 10 characters, then submit is disabled and the requirement is stated. When submitted, then an audit entry records actor, time (server), action, reason, and before/after.
- **AC-5:** Given I accepted a finding, when I press `Z` within 8s, then the decision reverts and the audit log shows both the decision and the undo. After 8s, changing it requires a reason.
- **AC-6:** Given the analyzer discarded findings that failed citation validation, then the analysis summary shows the discarded count. A discarded finding never appears in the list.
- **AC-7:** Given a low-confidence finding, then it has a dashed border and the "Needs careful review" label, and Accept is enabled only after the cited clause has been opened.
- **AC-8:** No finding is ever accepted without a human action (no auto-accept code path; verified by test).
- **AC-9:** Given two reviewers decide the same finding, when the second submits, then they see a conflict banner naming the first decider and their reason, with Keep theirs / Override (reason required).
- **AC-10:** Given findings without a decision exist, then Sign off is disabled and the report shows the count with links to them.
- **AC-11:** Given a report is signed, when any decision changes, then a new report version is created, and v1 stays viewable and marked "Superseded".
- **AC-12:** Audit entries have no edit or delete UI, and the audit log JSON export matches what is on screen.

### 5.2 Streaming, presence and reconnect
- **AC-13:** Given analysis is streaming and I have a finding selected or am scrolled away from the top, when a new finding arrives, then my scroll position and focus do not change, and a "N new findings" control appears.
- **AC-14:** Given a finding is still streaming, then its decision controls are disabled with "Finding still being written".
- **AC-15:** Given another reviewer is viewing a finding, then their avatar appears on it within 2s, with their name available on hover/focus.
- **AC-16:** Given the WebSocket drops (socket close, or heartbeat dead after 30s), then immediately on detection the indicator shows "Reconnecting" and decision controls are disabled with a reason; typed comment and reason drafts are preserved.
- **AC-17:** Given a finding was interrupted mid-stream, when the connection resumes and replay ends, then the draft row is replaced by the persisted finding in the same list position, with no duplicate row, or it is removed with the discard note.
- **AC-18:** Given a decision was submitted but not acknowledged before disconnect, when reconnected, then the UI shows either "Saved" (if the server has it) or "Not saved: Submit again", and never auto-resubmits.
- **AC-19:** Given others made changes during my disconnect, when reconnected, then the changes are applied and summarized ("While you were away: …").

### 5.3 Upload
- **AC-20:** Given I drop an unsupported or oversized file, then an inline message names the file and the limit, and other files continue.
- **AC-21:** Given a password-protected, image-only, or partially parsed file, then the specific message from 4.2 is shown, with Replace/Remove (and Continue anyway for a partial parse). The report records unparsed pages.
- **AC-22:** Upload works with keyboard only (the Browse control), and progress is exposed as `role="progressbar"` with a text value.

### 5.4 Accessibility (WCAG 2.2 AA)
- **AC-23 (keyboard-only full flow):** Using only the keyboard, a tester can create a project, upload, review and decide every finding (including reasons), comment, preview, export, and sign off. There are no traps; a visible focus ring is always on screen and not obscured by sticky bars (2.4.11).
- **AC-24 (streamed announcements):**
  - A polite live region announces new findings as a batched summary at most every 5s: "3 new findings: 1 critical, 2 medium." It never announces each token.
  - Critical findings are included in the batch, not interrupting (assertive is reserved for connection loss and analysis failure).
  - Users can mute stream announcements in settings.
- **AC-25 (focus management):**
  - Opening a popover or inline editor moves focus into it; closing returns focus to the trigger.
  - After a decision, focus moves to the next "Needs decision" finding (setting: stay/advance), and the change is announced ("Accepted F-0142. Next: F-0143, High").
- **AC-26 (200% zoom / reflow):** At 200% zoom and at a 320px-equivalent width, all content and functions are available without two-dimensional scrolling (document text excepted). The split view becomes tabs.
- **AC-27 (reduced motion):** With `prefers-reduced-motion`, there is no smooth scrolling, pulsing, shimmer, or height animation, and streamed text appears in chunks.
- **AC-28 (color independence):** With a grayscale filter, a tester can identify every finding's severity and decision state (label + icon + underline style), and can tell overlapping highlights apart.
- **AC-29 (contrast):** All text/background pairs used come from §2.4, and an automated axe check reports 0 contrast violations on the review, upload, and report screens in both themes.
- **AC-30 (targets and shortcuts):** Interactive targets are ≥24×24 px (2.5.8). Single-key shortcuts can be turned off or remapped (2.1.4), and are inactive while typing in text fields.
- **AC-31 (screen reader semantics):**
  - The findings list is a `listbox` or a `list` with roving focus.
  - Each finding's accessible name includes severity, title, control, and decision state.
  - Highlights expose their linked findings via `aria-describedby`.
  - The confidence meter has a text equivalent.
- **AC-32 (redundant entry, 3.3.7):** Reason text is not lost on validation errors, reconnects, or when switching findings.

---

## 6. Open questions to flag to Chief of Staff
1. **Roles:** engineering has owner/reviewer only. Who may sign off: owner only? Design assumes **owner signs off; reviewers decide and comment**.
2. **Conflict policy:** engineering rejects stale decisions (`version_conflict`). The design shows the winner + reason and offers Override as a new decision on the current version, with a reason required. Confirm that Override is allowed.
3. **What "Edit" means:** which fields can be edited (severity? control mapping? remediation?), and is the edited finding stored as a new version?
4. **Confidence:** engineering stores `confidence` 0..1, calibrated (ECE) on the gold set. Design shows **bands only**, not the number. Agree on the band thresholds and the 'Needs review' sort (design: within the severity group; engineering AC-7: after confident findings).
5. **Document view:** design assumes a **parsed-text view** (char offsets) rather than a rendered PDF with overlay highlights, which is much simpler. Confirm, and confirm whether partial parses exist (today they are pass/fail).
6. **Multiple frameworks per document:** findings from different frameworks can cite the same clause (overlap is designed for this). Should the report be per framework or combined?
7. **Internal Policy pack:** is authoring a custom pack in scope, or is it a fixed sample pack? I assumed fixed for the MVP.
8. **Sign-off:** the brief says "audit-ready report with evidence trail" and engineering puts signed reports out of scope. Design: attestation in the audit log + version lock. Confirm this is enough for the demo.
9. **Projects vs documents:** the API lists "projects", but the concept only mentions documents. Can a project hold several documents, and is there one report per document or per project?
10. **Offline decisions:** the MVP is read-only while disconnected. Confirm that this is acceptable versus an offline outbox.
11. **Data sensitivity:** will the demo use only synthetic or public contracts? Does the UI need PII redaction or a "do not upload real data" notice? (I'd add the notice.)
12. **Streaming granularity:** token-level `finding.delta` is on engineering's cut list. If it is cut, findings arrive whole: drop the `streaming` card state and keep the batch announcements. If presence is cut (also on the list), hide avatars; nothing else depends on them.
13. **@mentions and threads** are out of scope in engineering; the design removed them. **Escalate** needs an assignee, but there is no notification system in the MVP. Should Escalate just set a state + assignee shown in the list?

**MVP cut suggestions** (to fit 2-3 weeks; consistent with engineering's cut order): drop the ⌘K palette, presence cursors in the document, batch actions, and comment editing. Keep: streaming list + highlights, decisions with reasons + undo, presence avatars, reconnect/replay, audit log, and report with sign-off.
