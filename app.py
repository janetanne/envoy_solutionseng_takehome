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

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    print("/settings was hit")
    
    if request.method == 'POST':
        data = request.get_json()
        print("post request: ", data)

        # extract payload from request, check that it's a number
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
    print("webhook endpoint hit")
    event = request.get_json()

    # parse needed info
    event_type = event.get("meta", {}).get("event")
    attributes = event.get("payload", {}).get("attributes", {})
    full_name = attributes.get("full-name", "N/A") # defaults to N/A if name isn't present

    print(f"RECEIVED EVENT: {event_type} for {full_name}")

    


    return "200 OK", 200

    # try:

    #     attributes = event["data"]["attributes"]
    #     signed_in_at = attributes["signed-in-at"]
    #     signed_out_at = attributes["signed-out-at"]

    #     # this converts times from iso into datetime object 
    #     sign_in_time = datetime.fromisoformat(signed_in_at.rstrip("Z"))
    #     sign_out_time = datetime.fromisoformat(signed_out_at.rstrip("Z"))

    #     # this calculates the duration
    #     duration = int((sign_out_time - sign_in_time).total_seconds() / 60)
    #     allowed = config["allowed_minutes"]

    #     if duration > allowed:
    #         message = f"Visitor overstayed by {duration - allowed} minutes."
    #     else:
    #         message = "Visitor left on time."

    #     return jsonify({"message": message}), 200

    # except Exception as e:
    #     return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050, debug=True)