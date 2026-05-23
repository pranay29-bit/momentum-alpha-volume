import requests
import pandas as pd

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.nseindia.com/",
}


def get_result_date(symbol: str) -> str:

    symbol = symbol.replace(".NS", "").upper()

    try:
        session = requests.Session()

        # Important for NSE cookies
        session.get(
            "https://www.nseindia.com",
            headers=HEADERS,
            timeout=10,
        )

        url = (
            "https://www.nseindia.com/api/"
            "event-calendar?index=equities"
        )

        r = session.get(
            url,
            headers=HEADERS,
            timeout=10,
        )

        data = r.json()

        events = data.get("data", [])

        for item in events:

            sym = str(item.get("symbol", "")).upper()

            purpose = str(item.get("purpose", "")).lower()

            if sym != symbol:
                continue

            if (
                "result" in purpose
                or "financial" in purpose
                or "quarterly" in purpose
            ):

                dt = (
                    item.get("date")
                    or item.get("bm_date")
                    or item.get("event_date")
                )

                if dt:
                    try:
                        return pd.to_datetime(dt).strftime("%d-%b-%Y")
                    except Exception:
                        pass

    except Exception as e:
        print(f"Result date fetch failed for {symbol}: {e}")

    return "—"
