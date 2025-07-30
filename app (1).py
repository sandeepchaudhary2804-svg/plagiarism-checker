
from flask import Flask, request, jsonify, send_from_directory
import requests
import base64
import time
import os

app = Flask(__name__, static_url_path='', static_folder='.')

# Replace these with your actual Copyleaks credentials
COPYLEAKS_EMAIL = "your-email@example.com"
COPYLEAKS_API_KEY = "your-api-key"

def get_access_token():
    url = "https://id.copyleaks.com/v3/account/login/api"
    data = {"email": COPYLEAKS_EMAIL, "key": COPYLEAKS_API_KEY}
    res = requests.post(url, json=data)
    if res.status_code != 200:
        raise Exception("Authentication failed: " + res.text)
    return res.json()['access_token']

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/check', methods=['POST'])
def check_plagiarism():
    try:
        text = request.json.get('text')
        if not text:
            return jsonify({"error": "No text provided"}), 400

        token = get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        scan_id = "scan-" + str(hash(text))

        submit_url = f"https://api.copyleaks.com/v3/scans/submit/{scan_id}"
        data = {
            "base64": base64.b64encode(text.encode()).decode(),
            "properties": {"sandbox": True}
        }
        submit_res = requests.put(submit_url, json=data, headers=headers)
        if submit_res.status_code not in [200, 201]:
            return jsonify({"error": "Submission failed", "details": submit_res.text}), 500

        time.sleep(45)

        result_url = f"https://api.copyleaks.com/v3/scans/{scan_id}/result"
        result = requests.get(result_url, headers=headers)

        if result.status_code != 200:
            print("Copyleaks API error:", result.text)
            return jsonify({"error": "Scan not ready or failed"}), 500

        data = result.json()
        plagiarism_percent = data[0]["results"][0]["score"]
        matched_url = data[0]["results"][0]["url"]

        return jsonify({
            "plagiarism_percent": plagiarism_percent,
            "matched_url": matched_url
        })

    except Exception as e:
        print("Error in /check:", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
