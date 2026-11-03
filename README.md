# iphoneduo-availability

Watches Apple Hong Kong in-store pickup stock for one part number. A GitHub Actions workflow runs `check.py` every 10 minutes and commits `status.json` when the stock status at any store changes.

Setup: set the repository variable `PART_NUMBER` (e.g. `MK2E4ZA/A` = iPhone Duo 256GB Night Sky), and optionally `LOCATION` (default `Yau Tsim Mong`).
