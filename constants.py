import os

from dotenv import load_dotenv

load_dotenv()

ROBINHOOD_USERNAME = os.getenv("ROBINHOOD_USERNAME")
ROBINHOOD_PASSWORD = os.getenv("ROBINHOOD_PASSWORD")
ROBINHOOD_ACCOUNT_NUMBER = os.getenv("ROBINHOOD_ACCOUNT_NUMBER")
CIK = os.getenv("CIK")

_required = {
    "ROBINHOOD_USERNAME": ROBINHOOD_USERNAME,
    "ROBINHOOD_PASSWORD": ROBINHOOD_PASSWORD,
    "ROBINHOOD_ACCOUNT_NUMBER": ROBINHOOD_ACCOUNT_NUMBER,
    "CIK": CIK
}

missing = [k for k, v in _required.items() if not v]
if missing:
    raise ValueError(f"Missing required .env variables: {', '.join(missing)}")
