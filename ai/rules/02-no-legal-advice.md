# Rule 02: No legal advice; always show the disclaimer

**Disclaimer text** (render verbatim on the findings panel, every report page footer, and every remediation card):

> This tool provides automated analysis to support review by qualified professionals. It is not legal advice, does not establish compliance with any law or standard, and may contain errors. Findings and suggested language must be reviewed by appropriately qualified legal and compliance personnel before reliance.

**Wording rules for all agent output**
| Don't | Do |
|-------|----|
| "You are non-compliant with GDPR." | "Clause 9.2 does not set a breach-notification timeframe, which GDPR-33.2 (Art. 33(2)) expects." |
| "This contract is legally invalid." | "The text references SCC decision 2010/87/EU, which has been repealed." |
| "You must sign this clause." | "Example language that would address the gap: …" |
| "You will be fined." | (omit; penalties are out of scope) |

- The Verifier strips and flags any output containing `(?i)\b(you are|is) (non-)?compliant\b|\blegally (binding|invalid|required)\b|\byou (must|should) (sign|accept)\b` (flag `advice_language`).
- No jurisdiction-specific opinions beyond the control card's content. No predictions of regulator or court behaviour.
- Product copy calls them "findings" and "suggestions", never "opinions" or "advice".
