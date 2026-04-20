# Prague Migration Status

## Done
- Prague values are applied in the active scrapers.
- `BRAVIS` is disabled for the Prague-only build.
- Active scrapers passed a Prague-only smoke check.
- `REMAX`: Prague region id confirmed as `19`.
- `REALCITY`: Prague slug/id confirmed as `hlavni-mesto-praha-1` / `1`.
- `UlovDomov`: Prague bounds confirmed as `50.177403,14.7067945` / `49.9419363,14.2244533`.
- `EuroBydleni`: Prague region code `19` is exposed in page HTML.
- `Bezrealitky`: Prague `regionOsmIds` confirmed as `R435514`.
- `Sreality`: Prague works with `locality_region_id=10` and no district filter.

## Left
- Use a fresh `FOUND_OFFERS_FILE` before the first Prague rollout.
