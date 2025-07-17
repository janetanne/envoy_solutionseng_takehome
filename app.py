import os
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests

# this loads the environment variables - in this case it's the API key
load_dotenv()

app = Flask(__name__)

ENVOY_API_KEY = os.getenv('ENVOY_API_KEY')
ENVOY_API_URL = "https://api.envoy.com/v1"

## function for sending the message back to the Envoy app

def post_visitor_message(entry_id, message):
    url = f"https://api.envoy.com/v1/entries/{entry_id}"

    headers = {
        "X-Api-Key": ENVOY_API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "entry": {
            "privateNotes": message
        }
    }

    response = requests.post(url, headers=headers, json=data)
    print("Visitor comment logged:", response.status_code, response.text)

## ROUTES

# for the sake of a POC (i.e. no need to set up a DB to store visitor time)
# setting the in-memory config storage that will reset when server restarts

config = {
    "allowed_minutes": 180
}

@app.route('/settings', methods=['POST'])
def settings():
    data = request.get_json()

    # extract payload from request, validate that it's a number
    try:
        input_value = data.get("payload", {}).get("allowed_minutes")
        # converts input value to int, removes whitespace
        minutes = int(str(input_value).strip())
    except (ValueError, TypeError):
        return jsonify({"error": "Value must be a number"}), 400

    # validate that it's between 0-180
    if 0 <= minutes <= 180:
        config["allowed_minutes"] = minutes
        return jsonify({
            "allowed_minutes": {
                                    "value": str(config["allowed_minutes"])
                               }
            }), 200
    else:
        return jsonify({"error": "Allowed minutes must be between 0 and 180 minutes"}), 400


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    print("********** webhook endpoint hit ***********")
    event = request.get_json()

    # parse needed event type
    event_type = event.get("meta", {}).get("event")

    # check config from installer setup JUST IN CASE
    config = event.get("meta", {}).get("config", {})
    allowed_input = config.get("allowed_minutes", {}).get("value", "180") # fallback to 180 if config isn't present

    if allowed_input and allowed_input.strip().isdigit():
        allowed_minutes = int(allowed_input.strip())
    
    else: 
        allowed_minutes = 180
    
    # parse data from event
    attributes = event.get("payload", {}).get("attributes", {})
    full_name = attributes.get("full-name", "N/A") # defaults to N/A if name isn't present

    if event_type == "entry_sign_in":
        message = f"{full_name} signed in"
        # get entry id for sign-in
        entry_id = event.get("payload", {}).get("id")
        if entry_id:
            post_visitor_message(entry_id, message)
        return jsonify({"message": message}), 200

    if event_type == "entry_sign_out":
        try:
            signed_in_at = attributes.get("signed-in-at")
            signed_out_at = attributes.get("signed-out-at")

            if not signed_in_at or not signed_out_at:
                raise ValueError("Missing signed-in or signed-out timestamp")
            
            # convert timestamp into datetime object
            sign_in_time = datetime.fromisoformat(signed_in_at.replace(" UTC", "+00:00"))
            sign_out_time = datetime.fromisoformat(signed_out_at.replace(" UTC", "+00:00"))

            # calculate duration
            duration = int((sign_out_time - sign_in_time).total_seconds() / 60)

            # check duration
            if duration > allowed_minutes:
                message = f"{full_name} overstayed by {duration - allowed_minutes} minutes."

            else:
                message = f"{full_name} left on time :)"
            
            # post to Envoy API
            entry_id = event.get("payload", {}).get("id")
            if entry_id:
                post_visitor_message(entry_id, message)

            return jsonify({"message": message}), 200
        
        # catch any errors during sign-out
        except Exception as e:
            print(f"Error during sign-out: {e}")
            return jsonify({"message": f"Error: {str(e)}"}), 200
    
    return jsonify({"message": "No action needed"}), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050, debug=True)