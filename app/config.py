import os

from dotenv import load_dotenv

load_dotenv()

SWEDAVIA_BASE_URL = "https://api.swedavia.se/flightinfo/v2"

VALID_AIRPORTS = [
    "ARN", "GOT", "MMX", "BMA", "LLA", "UME",
    "VBY", "KRN", "RNB", "VST", "ORB", "NYO",
]


def get_api_key() -> str:
    key = os.getenv("SWEDAVIA_API_KEY")
    if not key:
        raise RuntimeError("SWEDAVIA_API_KEY is not set. Add it to your .env file.")
    return key
