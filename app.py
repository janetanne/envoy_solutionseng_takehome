import os
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# this loads the environment variables - in this case it's the API key
load_dotenv()

app = Flask(__name__)

ENVOY_API_KEY = os.getenv('ENVOY_API_KEY')
ENVOY_API_URL = "https://api.envoy.com/v1"

headers = {
    "X-Api-Key": ENVOY_API_KEY,
    "Content-Type": "application/json"
}

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
        return jsonify({"message": f"Sign-in logged for {full_name}"}), 200

    if event_type == "entry_sign_out":


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050, debug=True)