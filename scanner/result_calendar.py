import requests
import pandas as pd
from datetime import datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.nseindia.com/",
}


def get_result_date(symbol: str) -> str:
    """
    Fetch next/latest quarterly result declaration date from NSE.
    Returns date string or '—'
    """

    symbol = symbol.replace(".NS", "").upper()

    try:
        session = requests.Session()

        # NSE requires homepage hit first
        session.get(
            "https://www.nseindia.com",
            headers=HEADERS,
            timeout=10,
        )

        url = (
            f"https://www.nseindia.com/api/"
            f"corporate-announcements"
            f"?index=equities&symbol={symbol}"
        )

        r = session.get(url, headers=HEADERS, timeout=10)

        data = r.json()

        if not isinstance(data, list):
            return "—"

        today = datetime.today().date()

        result_dates = []

        for item in data:

            subject = str(item.get("subject", "")).lower()

            if (
                "financial results" in subject
                or "quarterly results" in subject
                or "results" in subject
            ):

                dt = (
                    item.get("broadcastDate")
                    or item.get("bm_date")
                    or item.get("date")
                )

                if not dt:
                    continue

                try:
                    parsed = pd.to_datetime(dt).date()

                    if parsed >= today:
                        result_dates.append(parsed)

                except Exception:
                    pass

        if result_dates:
            return min(result_dates).strftime("%d-%b-%Y")

    except Exception:
        pass

    return "—"
