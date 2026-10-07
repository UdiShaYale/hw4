# Design changes

Three visual changes, each aimed at the same end: a store that looks
deliberate, reads clearly, and gives a browsing shopper a reason to keep going.
All within the site's blue visual style.

---

## 1. A distinct typeface for the nav bar

**What changed.** The navigation bar now uses a serif face (Georgia) while the
page content stays sans-serif (Segoe UI). Two CSS variables, `--font-nav` and
`--font-body`, make the split explicit; the nav sets `font-family: var(--font-nav)`
and everything below inherits the body sans.

**Why a customer stays and buys.** The serif masthead reads as a settled,
collegiate brand — the kind of shop that has a storefront on Broadway, not a
pop-up. That first impression of legitimacy is what keeps a first-time visitor
browsing instead of bouncing. The contrast also draws a clear line between
"this is the brand / the chrome" and "this is the product information,"so the
eye lands on the content that actually sells.

**Verified.** Nav renders `Georgia, "Times New Roman", Cambria, serif`; the page
`<h1>` renders the Segoe UI sans stack. Two visibly different faces.

## 2. Bigger, differently-coloured category label on each product card

**What changed.** The category line on a product card (e.g. "QUARTER-ZIP
PULLOVER") went from 0.72rem in mid-blue to **0.9rem in teal** (`--accent-teal`,
`#0b7ea8`). It keeps the uppercase, letter-spaced, bold treatment.

**Why a customer stays and buys.** On a grid of 100+ items in one blue palette,
the category was the same blue as the product name and quietly blended in. A
larger teal label is the first thing the eye catches on each card, so a shopper
scanning for "hoodie" or "quarter-zip" can triage the grid at a glance instead
of reading every name. Faster scanning means they reach the thing they want
before they lose patience — the difference between a sale and a back-button.
Teal sits beside blue on the wheel, so it reads as a deliberate accent, not a
clash.

**Verified.** Category computed at 14.4px / `rgb(11,126,168)`; the product name
stays 16px / navy `rgb(0,53,107)` — clearly two different colours.

## 3. Text content in the About Us right sidebar

**What changed.** The right column of About Us held only the Yale shield. It is
now a real sidebar: the shield plus three cards —

- **At a glance** — founded dates, location, "printed in house within 48 hours,"
  100+ styles in XS–XXL (fact labels in the same teal accent).
- **Visit the shop** — address, hours, email, phone.
- **Harvard–Yale** — a short, navy accent card pointing at The Game and nudging
  shoppers to check sizes with the assistant.

**Why a customer stays and buys.** A wall of history with an empty margin asks a
lot of patience. The sidebar turns dead space into the answers a hesitant buyer
actually wants before paying a student-run shop: *where are you, when are you
open, how fast do you ship, do you have my size.* Concrete details — a real
address, a 48-hour turnaround, full size range — build the trust that converts a
reader into a buyer, and the Harvard–Yale card adds urgency with a clear next
step back into the catalogue.

**Verified.** Three sidebar cards render ("At a glance", "Visit the shop",
"Harvard–Yale") with four fact rows, 300px wide on desktop, wrapping full-width
on narrow screens.

---

## Checks

- `tsc -b` and `npm run build` pass; no browser console errors.
- All three changes verified live with computed styles and screenshots.
- Blue visual style preserved throughout; teal is a single cool-toned accent.
