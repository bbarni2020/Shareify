import os
from flask import Flask, jsonify, request
import requests
import time

app = Flask(__name__)

def cloud_full(base_url, jwt_token, command, method, shareify_jwt, wait_time, body={}):
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    
    if shareify_jwt:
        headers["X-Shareify-JWT"] = shareify_jwt

    payload = {
        "command": command,
        "method": method,
        "body": body
    }

    r = requests.post(f"{base_url}/cloud/command", json=payload, headers=headers)
    command_ids = r.json().get("command_ids", [])
    
    if not command_ids:
        return {"error": "No command_ids returned"}
    
    time.sleep(wait_time)
    
    params = [("command_id", cid) for cid in command_ids]
    params.append(("jwt_token", jwt_token))
    
    r2 = requests.get(f"{base_url}/cloud/response", headers=headers, params=params)
    response_data = r2.json()
    
    for command_id, command_response in response_data.get("responses", {}).items():
        if "response" in command_response:
            return command_response["response"]
        else:
            return command_response

@app.route('/', methods=['GET'])
def index():
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
        else:
            data = request.args.to_dict()
        
        base_url = 'https://bridge.bbarni.hackclub.app'
        jwt_token = data.get('jwt_token')
        command = data.get('command')
        method = data.get('method')
        shareify_jwt = data.get('shareify_jwt')
        wait_time = int(data.get('wait_time', 2))
        body = data.get('body', {})
        result = cloud_full(base_url, jwt_token, command, method, shareify_jwt, wait_time, body)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }), 500

application = app