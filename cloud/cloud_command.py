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
    poll_interval = 3
    attempts = 0
    
    while attempts < max_attempts:
        r = requests.post(f"{base_url}/cloud/command", json=payload, headers=headers)
        
        try:
            response_json = r.json()
            pass
        except Exception as e:
            pass
            attempts += 1
            time.sleep(poll_interval)
            continue
        
        if response_json and response_json.get("command_ids"):
            command_ids = response_json["command_ids"]
            pass
            break
        
        pass
        attempts += 1
        time.sleep(poll_interval)
    else:
        pass
        return {"error": "No command_ids returned after max attempts"}
    
    params = [("command_id", cid) for cid in command_ids]
    params.append(("jwt_token", jwt_token))
    
    max_response_attempts = 30
    response_poll_interval = 3
    response_attempts = 0
    
    while response_attempts < max_response_attempts:
        r2 = requests.get(f"{base_url}/cloud/response", headers=headers, params=params)
        
        try:
            response_data = r2.json()
            pass
        except Exception as e:
            pass
            response_attempts += 1
            time.sleep(response_poll_interval)
            continue
        
        for command_id, command_response in response_data.get("responses", {}).items():
            pass
            
            if command_response.get("completed", False):
                if "response" in command_response and command_response["response"] is not None:
                    pass
                    return command_response["response"]
                else:
                    pass
                    return command_response
            else:
                pass
        
        response_attempts += 1
        time.sleep(response_poll_interval)
    
    pass
    return {"error": "Command timeout - no completed response received", "raw_data": response_data}

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
    
        
        if not command or not method:
            pass
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: command and method are required',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }), 400
        
        if not jwt_token:
            pass
            return jsonify({
                'success': False,
                'error': 'Missing JWT token',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }), 401
        
        result = cloud_full(base_url, jwt_token, command, method, shareify_jwt, wait_time, body)
        
        if result is None:
            return jsonify({
                'success': False,
                'error': 'No response received from bridge server',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }), 500
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }), 500

application = app