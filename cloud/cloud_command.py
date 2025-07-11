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

    max_attempts = 10
    poll_interval = 1
    attempts = 0
    
    while attempts < max_attempts:
        r = requests.post(f"{base_url}/cloud/command", json=payload, headers=headers)
        print(r.text)
        response_json = r.json()
        
        if response_json and response_json.get("command_ids"):
            command_ids = response_json["command_ids"]
            break
        
        attempts += 1
        time.sleep(poll_interval)
    else:
        return {"error": "No command_ids returned after max attempts"}
    
    params = [("command_id", cid) for cid in command_ids]
    params.append(("jwt_token", jwt_token))
    
    r2 = requests.get(f"{base_url}/cloud/response", headers=headers, params=params)
    response_data = r2.json()
    
    for command_id, command_response in response_data.get("responses", {}).items():
        if "response" in command_response:
            return command_response["response"]
        else:
            return command_response

@app.route('/', methods=['POST'])
def index():
    try:
        data = request.get_json() or {}
        
        base_url = 'https://bridge.bbarni.hackclub.app'
        
        jwt_token = data.get('jwt_token')
        if not jwt_token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                jwt_token = auth_header[7:]
        
        shareify_jwt = data.get('shareify_jwt')
        if not shareify_jwt:
            shareify_jwt = request.headers.get('X-Shareify-JWT')
        
        command = data.get('command')
        method = data.get('method')
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