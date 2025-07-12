import os
from flask import Flask, jsonify, request
import requests
import time

app = Flask(__name__)

def cloud_full(base_url, jwt_token, command, method, shareify_jwt, wait_time, body={}):
    print(f"DEBUG: cloud_full called with:")
    print(f"  base_url: {base_url}")
    print(f"  command: {command}")
    print(f"  method: {method}")
    print(f"  shareify_jwt: {'Present' if shareify_jwt else 'None'}")
    print(f"  wait_time: {wait_time}")
    print(f"  body: {body}")
    
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

    print(f"DEBUG: Request payload: {payload}")
    print(f"DEBUG: Request headers: {headers}")

    max_attempts = 10
    poll_interval = 1
    attempts = 0
    
    while attempts < max_attempts:
        print(f"DEBUG: Attempt {attempts + 1} - Posting to {base_url}/cloud/command")
        r = requests.post(f"{base_url}/cloud/command", json=payload, headers=headers)
        print(f"DEBUG: Response status: {r.status_code}")
        print(f"DEBUG: Response text: {r.text}")
        
        try:
            response_json = r.json()
            print(f"DEBUG: Parsed JSON: {response_json}")
        except Exception as e:
            print(f"DEBUG: JSON parsing error: {e}")
            attempts += 1
            time.sleep(poll_interval)
            continue
        
        if response_json and response_json.get("command_ids"):
            command_ids = response_json["command_ids"]
            print(f"DEBUG: Got command_ids: {command_ids}")
            break
        
        print(f"DEBUG: No command_ids found, retrying...")
        attempts += 1
        time.sleep(poll_interval)
    else:
        print("DEBUG: Max attempts reached, no command_ids")
        return {"error": "No command_ids returned after max attempts"}
    
    params = [("command_id", cid) for cid in command_ids]
    params.append(("jwt_token", jwt_token))
    
    print(f"DEBUG: Getting response with params: {params}")
    r2 = requests.get(f"{base_url}/cloud/response", headers=headers, params=params)
    print(f"DEBUG: Response status: {r2.status_code}")
    print(f"DEBUG: Response text: {r2.text}")
    
    try:
        response_data = r2.json()
        print(f"DEBUG: Parsed response data: {response_data}")
    except Exception as e:
        print(f"DEBUG: JSON parsing error on response: {e}")
        return {"error": "Invalid JSON response from bridge server"}
    
    for command_id, command_response in response_data.get("responses", {}).items():
        print(f"DEBUG: Processing command_id: {command_id}, response: {command_response}")
        if "response" in command_response:
            print(f"DEBUG: Returning response: {command_response['response']}")
            return command_response["response"]
        else:
            print(f"DEBUG: Returning command_response: {command_response}")
            return command_response
    
    print("DEBUG: No responses found in response data")
    return {"error": "No responses found", "raw_data": response_data}

@app.route('/', methods=['POST'])
def index():
    try:
        print("DEBUG: Received request")
        data = request.get_json() or {}
        print(f"DEBUG: Request data: {data}")
        print(f"DEBUG: Request headers: {dict(request.headers)}")
        
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
        
        print(f"DEBUG: Extracted parameters:")
        print(f"  jwt_token: {'Present' if jwt_token else 'None'}")
        print(f"  shareify_jwt: {'Present' if shareify_jwt else 'None'}")
        print(f"  command: {command}")
        print(f"  method: {method}")
        print(f"  wait_time: {wait_time}")
        print(f"  body: {body}")
        
        result = cloud_full(base_url, jwt_token, command, method, shareify_jwt, wait_time, body)
        
        print(f"DEBUG: Final result: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }), 500

application = app