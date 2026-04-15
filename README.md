# Copy Trading

Mirrors a hedge fund's 13F portfolio on Robinhood. Pulls the latest SEC filing, walks you through approving each position, then places fractional orders proportionally.

## Setup

```
pip install -r requirements.txt
cp .env.example .env  # fill in your values
```

## .env

```
ROBINHOOD_USERNAME=you@example.com
ROBINHOOD_PASSWORD=yourpassword
ROBINHOOD_ACCOUNT_NUMBER=123456789
CIK=2045724
```

- **ROBINHOOD_ACCOUNT_NUMBER** — Robinhood > Account > Investing > Settings > Personal Information > Account numbers
- **CIK** — SEC EDGAR identifier for the fund. Find it at [EDGAR company search](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=13F-HR). Situational Awareness LP (Leopold Aschenbrenner) = `2045724`

## Usage

```
python main.py
```

## Example

```
Starting login process...
How much to invest ($)? 2
Include BE — $0.45 (22.4%)? [y/N] y
Include LITE — $0.24 (12.2%)? [y/N] y
Include CRWV — $0.22 (11.2%)? [y/N] y
Include CORZ — $0.21 (10.7%)? [y/N] n
Include APLD — $0.14 (7.1%)? [y/N] y
...

────────────────────────────────────────
  Ticker     Amount   Weight
────────────────────────────────────────
  BE       $   0.45   22.4%
  LITE     $   0.24   12.2%
  CRWV     $   0.22   11.2%
  APLD     $   0.14    7.1%
────────────────────────────────────────
  TOTAL    $   1.05
────────────────────────────────────────

Place all orders? [y/N] y
```

## Notes

- Holdings come from the fund's most recent 13F filing (reported quarterly, ~45 day lag)
- Options positions are excluded (`include_options=False`)
- To mirror a different fund, change the `CIK` in `.env`
- `breakdown.py` prints a full holdings table + quarter-over-quarter changes if you just want to inspect without buying
