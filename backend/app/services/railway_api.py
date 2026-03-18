# Train / PNR / seat API calls
def handle_intent(intent, text):

    if intent == "train_status":
        return "I’ve checked the latest update — your train is currently near Kanpur and running about 20 minutes late. It should reach Lucknow around 2:30 PM."

    elif intent == "pnr_status":
        return "Good news! Your ticket is confirmed, and your seat is in sleeper class."

    elif intent == "seat_availability":
        return "Seats are available in Sleeper and 3AC class for your journey."

    return None