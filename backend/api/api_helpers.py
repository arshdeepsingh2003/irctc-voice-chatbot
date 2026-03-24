# api/api_helpers.py

from datetime import datetime


# ===================== HELPER (ROBUST SEARCH) =====================

def _find_train_data(data, depth=0):
    """
    Recursively searches nested dicts/lists for a dict
    containing 'train_number'.
    """
    if depth > 5:
        return None

    if isinstance(data, dict):
        if "train_number" in data:
            return data

        for value in data.values():
            result = _find_train_data(value, depth + 1)
            if result:
                return result

    elif isinstance(data, list):
        for item in data:
            result = _find_train_data(item, depth + 1)
            if result:
                return result

    return None


# ===================== PNR (HARDENED) =====================

def format_pnr_response(api_data: dict) -> str:
    """
    Formats PNR status. Handles multiple API structures.
    """
    try:
        raw = api_data.get("data", api_data)

        if isinstance(raw, list):
            raw = raw[0] if raw else {}

        if isinstance(raw, str):
            return f"🎫 PNR update: {raw}"

        if not isinstance(raw, dict):
            return "😔 Could not read PNR data."

        pnr        = raw.get("pnrNumber") or raw.get("pnr_number") or "N/A"
        train_name = raw.get("trainName") or raw.get("train_name") or "N/A"
        train_no   = raw.get("trainNumber") or raw.get("train_number") or "N/A"
        doj        = raw.get("dateOfJourney") or raw.get("doj") or "N/A"
        from_stn   = raw.get("boardingPoint") or raw.get("from") or "N/A"
        to_stn     = raw.get("reservationUpto") or raw.get("to") or "N/A"
        cls        = raw.get("journeyClass") or raw.get("class") or "N/A"
        chart      = raw.get("chartStatus") or raw.get("chart_status") or "N/A"

        passengers = raw.get("passengerList") or raw.get("passengers") or []

        pax_lines = []
        for i, p in enumerate(passengers, 1):
            if isinstance(p, dict):
                booking = p.get("bookingStatus") or p.get("booking_status") or "N/A"
                current = p.get("currentStatus") or p.get("current_status") or "N/A"
                coach   = p.get("coachId") or p.get("coach") or ""
                berth   = p.get("berth") or p.get("seatNumber") or ""

                seat = f"Coach {coach}, Berth {berth}" if coach else current

                pax_lines.append(
                    f"  Passenger {i}: Booked as {booking} → Now {seat}"
                )

        pax_text = "\n".join(pax_lines) if pax_lines else "  Passenger details not available"

        return (
            f"🎫 PNR Status: {pnr}\n\n"
            f"🚂 Train: {train_name} ({train_no})\n"
            f"📅 Date: {doj}\n"
            f"🛤️ Route: {from_stn} → {to_stn}\n"
            f"💺 Class: {cls}\n"
            f"📋 Chart: {chart}\n\n"
            f"👥 Passengers:\n{pax_text}"
        )

    except Exception:
        return f"🎫 Raw PNR data:\n{str(api_data)[:400]}"


# ===================== TRAIN STATUS (FINAL FIX) =====================

def format_train_status_response(api_data: dict) -> str:
    """
    Robust train status formatter with multi-level unwrap.
    """
    try:
        # ── UNWRAP LEVELS ──
        level1 = api_data if isinstance(api_data, dict) else {}
        level2 = level1.get("data", level1)
        level3 = level2.get("data", level2)

        # Handle extra nesting
        if isinstance(level3, dict) and "train_number" not in level3:
            inner = level3.get("data", level3)
        else:
            inner = level3

        # Fallback search if still not found
        if not isinstance(inner, dict) or "train_number" not in inner:
            inner = _find_train_data(api_data)

        if not inner:
            return "😔 No live train data found. The train may not be running today."

        # ── EXTRACT DATA ──
        train_no   = inner.get("train_number", "N/A")
        train_name = inner.get("train_name", "N/A")
        delay      = inner.get("delay", 0)

        current_station = inner.get("current_station_name", "").replace("~", "").strip()
        platform        = inner.get("platform_number")
        status_code     = inner.get("status", "")
        message         = inner.get("new_message", "")
        actual_arrival  = inner.get("actual_arrival_time", "")

        source = inner.get("source_stn_name", inner.get("source", "N/A"))
        dest   = inner.get("dest_stn_name", inner.get("destination", "N/A"))

        # ── BUILD RESPONSE ──
        lines = [
            f"🚂 {train_name} ({train_no})",
            f"🛤️ Route: {source} → {dest}",
            ""
        ]

        # Destination reached
        if status_code == "D":
            lines.append(f"🏁 {message or 'Train has reached destination'}")
            lines.append(f"📍 Station: {current_station}")

            if actual_arrival:
                lines.append(f"🕒 Arrival: {actual_arrival}")

            if platform:
                lines.append(f"🚉 Platform: {platform}")

        # Running
        else:
            lines.append(f"📍 Current Location: {current_station}")
            lines.append(f"⏱️ Delay: {delay} minutes")

        return "\n".join(lines)

    except Exception as e:
        return f"⚠️ Error formatting train data: {str(e)}"


# ===================== SEAT AVAILABILITY =====================

def format_seat_availability_response(api_data: dict) -> str:
    try:
        d = api_data.get("data", {})
        avail_list = d if isinstance(d, list) else d.get("availability", [])

        if not avail_list:
            return "😔 No seat availability data found."

        lines = []
        for item in avail_list[:6]:
            date   = item.get("date", "N/A")
            status = item.get("availabilityStatus", "N/A")

            if "AVAILABLE" in str(status).upper():
                icon = "🟢"
            elif "WL" in str(status).upper():
                icon = "🟡"
            elif "RAC" in str(status).upper():
                icon = "🟠"
            else:
                icon = "🔴"

            lines.append(f"{icon} {date}: {status}")

        return "🪑 Seat Availability:\n\n" + "\n".join(lines)

    except Exception as e:
        return f"Error formatting availability: {str(e)}"


# ===================== DATE PARSER =====================

def parse_date_for_api(date_str: str):
    try:
        dt = datetime.strptime(date_str.strip(), "%d %b %Y")
        return dt.strftime("%Y%m%d")
    except:
        return None