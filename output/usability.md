# Usability improvements

Two bug fixes the shopper reported, plus four enhancements — two front-end, two
back-end. Each entry says what changed and who it helps.

---

## Bug fixes

### 1. "colour" → "color" in the search placeholder

`Products.tsx` — the search box read *"Search by name, colour, team or tag"*.
Changed to the American spelling to match the rest of a US university store.

**Helps:** a small credibility thing — inconsistent spelling makes a storefront
look unfinished, and the catalogue's own color values are spelled "color".

### 2. Last-name field spilling out of the Create Account card

The two name fields sit in a `display: grid` two-column row. A text input has an
intrinsic width (~20 characters), and a grid item defaults to `min-width: auto`,
which refuses to shrink below that intrinsic size — so the second column pushed
~175 px past the edge of the card.

**Fix** (`index.css`): `width: 100%` on `.field input` and `min-width: 0` on
`.field`, so the input fills its column and the column is free to shrink.

**Helps:** the signup form no longer looks broken. Measured: the last-name
input went from **175 px of overflow to sitting 1 px inside** the card; both
columns are now an equal 176 px.

---

## Front-end enhancement 1 — Sort control on Products

A **Sort** dropdown in the Products toolbar: *Featured* (the default order),
*Price: low to high*, *Price: high to low*, *Name: A–Z*.

Sorting happens on the client. All matching products are already fetched in one
request, so reordering is instant with no extra round trip, and *Featured*
preserves the server's relevance order.

**Helps the shopper and the business:** a budget-conscious student can put the
cheapest items first in one click — the single most common way people shop
apparel. Making price-sorting trivial lifts the odds a $32 tee gets seen and
bought rather than lost below the $98 jackets.

**Verified:** low-to-high leads with $32, high-to-low with $98 (the catalogue's
true min and max), and A–Z orders by name.

## Front-end enhancement 2 — Graceful image fallback

A new `ProductImage` component. If a photo is missing or fails to load, it swaps
the broken-image icon for a tasteful Yale-blue placeholder that keeps the
product's name as its `aria-label`. Used everywhere a product photo appears:
the Products grid, the assistant's match band, and the item page.

**Helps the shopper and the business:** one bad file path used to drop a grey
broken-image icon into the grid, which reads as "this shop is broken" and
costs trust on the exact screen where people decide to buy. Now the worst case
is a neutral placeholder, and the layout never shifts. It also keeps its
accessible label, so a screen reader still announces the product.

**Verified:** pointed a card at a non-existent file — the `<img>` was replaced
by the labelled placeholder, no broken icon, no console error.

---

## Back-end enhancement 1 — GZip compression

`GZipMiddleware` on the FastAPI app compresses JSON responses over ~0.5 KB. The
catalogue is mostly repetitive text — descriptions, search tags — which
compresses extremely well.

**Helps the shopper and the business:** the `/api/products` payload dropped from
**57 KB to 7.8 KB — 86 % smaller**. The catalogue paints faster, especially on
a phone on campus wifi, and the shop serves a fraction of the bandwidth for the
same traffic.

**Verified:** `content-encoding: gzip` on the response; raw 57,000 bytes vs
7,799 gzipped.

## Back-end enhancement 2 — Cache-Control on product images

`CachedStaticFiles` (a `StaticFiles` subclass) adds
`Cache-Control: public, max-age=86400` to every product photo. By default
StaticFiles sends only ETag/Last-Modified, so each repeat view still makes a
round trip to revalidate.

**Helps the shopper and the business:** a returning shopper — or anyone
scrolling back to a product they already saw — loads the photo straight from the
browser cache instead of re-fetching it, so cards and item pages feel instant.
The server also stops answering a request for every image it already sent. Image
paths change when a product does, so a one-day cache carries no risk of a stale
photo.

**Verified:** `Cache-Control: public, max-age=86400` present on an image
response; catalogue JSON stays uncached, as it should.

---

## Checks

- `tsc -b` and `npm run build` pass; no browser console errors.
- All four enhancements verified live, with the before/after numbers above.
- The database was not modified by any of this work.
