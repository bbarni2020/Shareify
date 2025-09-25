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

    max_attempts = 15
    poll_interval = 2
    attempts = 0
    
    while attempts < max_attempts:
        try:
            r = requests.post(f"{base_url}/cloud/command", json=payload, headers=headers, timeout=30)
            
            if r.status_code != 200:
                attempts += 1
                time.sleep(poll_interval)
                continue
                
            response_json = r.json()
            
            if response_json and response_json.get("command_ids"):
                command_ids = response_json["command_ids"]
                break
            elif response_json and response_json.get("error"):
                return {"error": f"Bridge server error: {response_json['error']}"}
                
        except requests.exceptions.RequestException as e:
            attempts += 1
            if attempts >= max_attempts:
                return {"error": f"Failed to connect to bridge server after {max_attempts} attempts: {str(e)}"}
            time.sleep(poll_interval)
            continue
        except Exception as e:
            attempts += 1
            time.sleep(poll_interval)
            continue
        
        attempts += 1
        time.sleep(poll_interval)
    else:
        return {"error": "No command_ids returned after max attempts"}
    
    params = [("command_id", cid) for cid in command_ids]
    params.append(("jwt_token", jwt_token))
    
    max_response_attempts = 30
    response_poll_interval = 2
    response_attempts = 0
    last_progress = {}
    is_chunked_transfer = False
    
    while response_attempts < max_response_attempts:
        try:
            r2 = requests.get(f"{base_url}/cloud/response", headers=headers, params=params, timeout=30)
            
            if r2.status_code != 200:
                response_attempts += 1
                time.sleep(response_poll_interval)
                continue
                
            response_data = r2.json()
            
            for command_id, command_response in response_data.get("responses", {}).items():
                
                if command_response.get("chunked", False):
                    is_chunked_transfer = True
                    if max_response_attempts < 60:
                        max_response_attempts = 60
                
                if command_response.get("completed", False):
                    if command_response.get("chunked", False):
                        chunks_received = command_response.get("chunks_received", 0)
                        total_chunks = command_response.get("total_chunks", 0)
                        
                        if total_chunks > 0 and chunks_received == total_chunks:
                            if "assembled_data" in command_response:
                                return command_response["assembled_data"]
                            elif "response" in command_response:
                                return command_response["response"]
                        else:
                            continue
                    else:
                        if "response" in command_response and command_response["response"] is not None:
                            return command_response["response"]
                        else:
                            return command_response
                            
                elif command_response.get("chunked", False):
                    chunks_received = command_response.get("chunks_received", 0)
                    total_chunks = command_response.get("total_chunks", 0)
                    
                    if command_id not in last_progress or last_progress[command_id] != chunks_received:
                        last_progress[command_id] = chunks_received
                        
                        if total_chunks > 0:
                            progress = (chunks_received / total_chunks) * 100
                        else:
                            progress = 0
                            
        except requests.exceptions.RequestException as e:
            response_attempts += 1
            if response_attempts >= max_response_attempts:
                return {"error": f"Network error while polling response: {str(e)}"}
            time.sleep(response_poll_interval)
            continue
        except Exception as e:
            response_attempts += 1
            time.sleep(response_poll_interval)
            continue
        
        response_attempts += 1
        
        if response_attempts > 20:
            response_poll_interval = min(response_poll_interval * 1.1, 5)
        
        time.sleep(response_poll_interval)
    
    return {"error": "Command timeout - response not received within time limit", "last_status": response_data if 'response_data' in locals() else None}

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