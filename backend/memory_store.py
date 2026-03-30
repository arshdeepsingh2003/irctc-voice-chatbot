# Manages conversation memory for each session.
# Stores user name, preferences, frequent trains, and recent context.
# Memory lives in RAM — resets when backend restarts.


from datetime import datetime
from collections import defaultdict, Counter

# In-memory store — keyed by session_id
# Each session has its own memory dict
_sessions: dict = defaultdict(lambda: {
    "user_name":        None,       # extracted from conversation
    "frequent_trains":  Counter(),  # train numbers mentioned
    "frequent_routes":  Counter(),  # from→to routes mentioned
    "last_intent":      None,       # last successfully completed intent
    "last_train":       None,       # last train number used
    "last_pnr":         None,       # last PNR checked
    "last_from":        None,       # last source station
    "last_to":          None,       # last destination station
    "facts":            [],         # any facts user mentioned about themselves
    "turn_count":       0,          # how many turns in this session
    "created_at":       datetime.now().isoformat(),
    "updated_at":       datetime.now().isoformat(),
})


def get_memory(session_id: str) -> dict:
    """Returns memory for a session."""
    return _sessions[session_id]


def update_memory(session_id: str, intent_result: dict, user_message: str):
    """
    Updates session memory based on the latest turn.
    Call this AFTER intent detection, BEFORE routing.
    """
    mem = _sessions[session_id]
    mem["turn_count"] += 1
    mem["updated_at"]  = datetime.now().isoformat()

    extracted = intent_result.get("extracted", {})
    intent    = intent_result.get("intent", "")

    # ── Extract user name ──
    # Look for patterns like "my name is X" or "I am X" or "call me X"
    import re
    name_patterns = [
        r"my name is (\w+)",
        r"i am (\w+)",
        r"call me (\w+)",
        r"i'm (\w+)",
        r"this is (\w+)",
    ]
    msg_lower = user_message.lower()
    for pattern in name_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            name = match.group(1).capitalize()
            # Filter out common false positives
            if name.lower() not in ["a", "the", "here", "back", "going", "trying", "asking"]:
                mem["user_name"] = name
                break

    # ── Track frequent trains ──
    train_no = extracted.get("train_number")
    if train_no:
        mem["frequent_trains"][train_no] += 1
        mem["last_train"] = train_no

    # ── Track frequent routes ──
    from_stn = extracted.get("from_station")
    to_stn   = extracted.get("to_station")
    if from_stn and to_stn:
        route = f"{from_stn.upper()}→{to_stn.upper()}"
        mem["frequent_routes"][route] += 1
        mem["last_from"] = from_stn.upper()
        mem["last_to"]   = to_stn.upper()

    # ── Track last PNR ──
    pnr = extracted.get("pnr_number")
    if pnr:
        mem["last_pnr"] = pnr

    # ── Track last completed intent ──
    if intent and intent != "general_query":
        mem["last_intent"] = intent

    # ── Extract user facts ──
    # Patterns like "I usually travel in 3AC" or "I travel from Delhi"
    fact_patterns = [
        r"i (usually|always|prefer|like|travel|go|come) (.{5,40})",
        r"i am (from|based in|living in) (\w+)",
    ]
    for pattern in fact_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            fact = f"User mentioned: '{user_message}'"
            if fact not in mem["facts"] and len(mem["facts"]) < 10:
                mem["facts"].append(fact)

    _sessions[session_id] = mem


def build_memory_context(session_id: str) -> str:
    """
    Builds a short memory summary string to inject
    into the Ollama prompt as context.
    """
    mem = get_memory(session_id)

    lines = []

    if mem["user_name"]:
        lines.append(f"User's name: {mem['user_name']}")

    if mem["last_intent"]:
        lines.append(f"Last query type: {mem['last_intent'].replace('_', ' ')}")

    if mem["last_train"]:
        lines.append(f"Last train asked about: {mem['last_train']}")

    if mem["last_pnr"]:
        lines.append(f"Last PNR checked: {mem['last_pnr']}")

    if mem["last_from"] and mem["last_to"]:
        lines.append(f"Last route: {mem['last_from']} to {mem['last_to']}")

    # Top 3 frequent trains
    top_trains = mem["frequent_trains"].most_common(3)
    if top_trains:
        train_list = ", ".join([t[0] for t in top_trains])
        lines.append(f"Frequently asked trains: {train_list}")

    # Top 2 frequent routes
    top_routes = mem["frequent_routes"].most_common(2)
    if top_routes:
        route_list = ", ".join([r[0] for r in top_routes])
        lines.append(f"Frequent routes: {route_list}")

    # User facts
    if mem["facts"]:
        lines.extend(mem["facts"][-3:])  # last 3 facts only

    if mem["turn_count"] > 0:
        lines.append(f"Conversation turns so far: {mem['turn_count']}")

    if not lines:
        return ""

    return "KNOWN CONTEXT ABOUT THIS USER:\n" + "\n".join(f"- {l}" for l in lines)


def clear_memory(session_id: str):
    """Clears memory for a session."""
    if session_id in _sessions:
        del _sessions[session_id]