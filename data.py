import re
import xml.etree.ElementTree as ET

import requests

from constants import EDGAR_USER_AGENT

EDGAR_HEADERS = {"User-Agent": EDGAR_USER_AGENT}


def get_positions(cik: str, include_options: bool = True) -> list[tuple[str, float]]:
    """
    Return the latest 13F holdings as (ticker, weight) pairs, sorted by weight desc.
    weight is a fraction of total portfolio value (0.0–1.0).
    Positions where a ticker cannot be resolved are skipped.
    """
    filings = _get_13f_filings(cik, limit=1)
    if not filings:
        return []

    holdings = _fetch_holdings(cik, filings[0]["accn"])

    if not include_options:
        holdings = [h for h in holdings if not h["put_call"]]

    total = sum(h["value"] for h in holdings)
    if total == 0:
        return []

    cusips = list({h["cusip"] for h in holdings})
    ticker_map = _cusips_to_tickers(cusips)

    resolved = [(ticker_map[h["cusip"]], h["value"]) for h in holdings if ticker_map.get(h["cusip"])]
    resolved_total = sum(v for _, v in resolved)
    if resolved_total == 0:
        return []

    positions = sorted(
        [(ticker, value / resolved_total) for ticker, value in resolved],
        key=lambda x: x[1], reverse=True,
    )
    return positions


# ── EDGAR ─────────────────────────────────────────────────────────────────────

def _get_13f_filings(cik: str, limit: int = 2) -> list[dict]:
    url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    r = requests.get(url, headers=EDGAR_HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    dates = filings.get("filingDate", [])
    accns = filings.get("accessionNumber", [])
    results = []
    for form, date, accn in zip(forms, dates, accns):
        if form == "13F-HR":
            results.append({"date": date, "accn": accn.replace("-", "")})
        if len(results) == limit:
            break
    return results


def _fetch_holdings(cik: str, accn: str) -> list[dict]:
    index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/index.json"
    r = requests.get(index_url, headers=EDGAR_HEADERS, timeout=15)
    r.raise_for_status()
    files = r.json().get("directory", {}).get("item", [])
    xml_name = next(
        (f["name"] for f in files if f["name"].lower().endswith(".xml") and "infotable" in f["name"].lower()),
        next((f["name"] for f in files if f["name"].lower().endswith(".xml") and f["name"] != "primary_doc.xml"), None),
    )
    if not xml_name:
        return []
    xml_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/{xml_name}"
    r2 = requests.get(xml_url, headers=EDGAR_HEADERS, timeout=30)
    r2.raise_for_status()
    return _parse_infotable(r2.text)


def _parse_infotable(xml_text: str) -> list[dict]:
    xml_text = re.sub(r'<(/?)[\w]+:', r'<\1', xml_text)
    xml_text = re.sub(r' xmlns[^"]*"[^"]*"', '', xml_text)
    root = ET.fromstring(xml_text)
    holdings = []
    for info in root.iter("infoTable"):
        shrs_el = info.find("shrsOrPrnAmt")
        holdings.append({
            "name": (info.findtext("nameOfIssuer") or "").strip(),
            "cusip": (info.findtext("cusip") or "").strip(),
            "value": int(info.findtext("value") or 0),
            "shares": int(shrs_el.findtext("sshPrnamt") or 0) if shrs_el is not None else 0,
            "share_type": (shrs_el.findtext("sshPrnamtType") or "").strip() if shrs_el is not None else "",
            "put_call": (info.findtext("putCall") or "").strip(),
        })
    return holdings


# ── CUSIP → ticker (OpenFIGI, free, no key required) ─────────────────────────

def _cusips_to_tickers(cusips: list[str]) -> dict[str, str]:
    """Batch-resolve CUSIPs to ticker symbols via the OpenFIGI API."""
    ticker_map: dict[str, str] = {}
    batch_size = 10  # OpenFIGI free tier allows 10 per request
    for i in range(0, len(cusips), batch_size):
        batch = cusips[i : i + batch_size]
        payload = [{"idType": "ID_CUSIP", "idValue": c} for c in batch]
        try:
            resp = requests.post(
                "https://api.openfigi.com/v3/mapping",
                json=payload,
                timeout=15,
            )
            resp.raise_for_status()
            for cusip, result in zip(batch, resp.json()):
                data = result.get("data", [])
                if data:
                    ticker_map[cusip] = data[0].get("ticker", "")
        except Exception:
            pass  # leave unresolved CUSIPs out of the map
    return ticker_map
