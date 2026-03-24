# api/railway_client.py
# Single place for all RapidAPI Indian Railway calls.
# Keeps API logic separate from business logic.

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY  = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "irctc1.p.rapidapi.com")

BASE_URL = f"https://{RAPIDAPI_HOST}"

# Standard headers for every request
def get_headers() -> dict:
    return {
        "x-rapidapi-key":  RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }


def fetch_pnr_status(pnr_number: str) -> dict:
    """
    Fetches PNR status from RapidAPI.
    Returns raw API response dict.
    """
    url = f"{BASE_URL}/api/v3/getPNRStatus"
    params = {"pnrNumber": pnr_number}

    return _make_request(url, params)


def fetch_train_status(train_number: str) -> dict:
    """
    Fetches live running status of a train.
    """
    url = f"{BASE_URL}/api/v1/liveTrainStatus"
    params = {
        "trainNo":   train_number,
        "startDay":  "1"          # 1 = today, 2 = yesterday
    }

    return _make_request(url, params)


def fetch_seat_availability(
    train_number: str,
    date: str,
    from_station: str,
    to_station: str,
    travel_class: str,
    quota: str = "GN"
) -> dict:
    """
    Checks seat availability for a train journey.
    date format: YYYYMMDD  e.g. 20250625
    """
    url = f"{BASE_URL}/api/v1/checkSeatAvailability"
    params = {
        "classType":    travel_class,
        "fromStationCode": from_station,
        "quota":        quota,
        "toStationCode": to_station,
        "trainNo":      train_number,
        "date":         date
    }

    return _make_request(url, params)


def fetch_train_between_stations(
    from_station: str,
    to_station: str,
    date: str
) -> dict:
    """
    Finds trains running between two stations on a date.
    """
    url = f"{BASE_URL}/api/v3/trainBetweenStations"
    params = {
        "fromStationCode": from_station,
        "toStationCode":   to_station,
        "dateOfJourney":   date
    }

    return _make_request(url, params)


def _make_request(url: str, params: dict) -> dict:
    """
    Internal helper — makes the actual HTTP GET request.
    Returns a standard dict with success/error info.
    """
    if not RAPIDAPI_KEY:
        return {
            "success": False,
            "error": "RAPIDAPI_KEY not set in .env file"
        }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, headers=get_headers(), params=params)
            response.raise_for_status()
            data = response.json()

            # RapidAPI returns status in the response body too
            if data.get("status") is False:
                return {
                    "success": False,
                    "error": data.get("message", "API returned no data")
                }

            return {
                "success": True,
                "data": data
            }

    except httpx.TimeoutException:
        return {"success": False, "error": "Railway API timed out. Please try again."}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            return {"success": False, "error": "Invalid API key. Check your .env file."}
        if e.response.status_code == 429:
            return {"success": False, "error": "API rate limit reached. Try again in a minute."}
        return {"success": False, "error": f"API error: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}