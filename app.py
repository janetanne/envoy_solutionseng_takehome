import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

# this loads the environment variables - in this case it's the API key
load_dotenv()

app = Flask(__name__)

ENVOY_API_TOKEN = os.getenv('ENVOY_API_TOKEN')
ENVOY_API_URL = "https://api.envoy.com/v1"

## ROUTES

# for the sake of a POC (i.e. no need to set up a DB to store visitor time)
# setting the in-memory config storage that will reset when server restarts)

config = {
    "allowed_minutes": 60
}

@app.route('/settings', methods=['GET', 'PATCH'])
def settings():
    if request.method == 'GET':
        return jsonify({
            "allowed_minutes": {
                "type": "number",
                "label": "Allowed visit in minutes",
                "value": config["allowed_minutes"],
                "help_text": "Set how long visitors are allowed to stay (0–180 minutes only)."
            }
        })

    if request.method == 'PATCH':
        data = request.get_json()
        input_value = data.get("allowed_minutes", {}).get("value")

        # this validates that the input value is an integer and between 0-180
        if isinstance(input_value, int) and (0 <= input_value <= 180):
            config["allowed_minutes"] = input_value
            return jsonify({"allowed_minutes": {"value": config["allowed_minutes"]}}), 200

        else:
            return jsonify({"error": "allowed_minutes must be an integer between 0 and 180"}), 400


if __name__ == '__main__':
    app.run(debug=True)