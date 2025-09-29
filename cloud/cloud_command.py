import os
import io
import base64
from flask import Flask, jsonify, request, send_file
import requests
import time

app = Flask(__name__)

def retrieve_stored_file(base_url, file_storage_response):
    try:
        file_id = file_storage_response.get("file_id")
        password = file_storage_response.get("password")
        original_type = file_storage_response.get("original_type", "text")
        filename = file_storage_response.get("filename")
        
        if not file_id or not password:
            print("Missing file_id or password in storage response")
            return None
        
        print(f"Retrieving file {file_id} from storage...")
        
        retrieve_response = requests.post(
            f"{base_url}/cloud/file/retrieve",
            json={"file_id": file_id, "password": password},
            timeout=30
        )
        
        if retrieve_response.status_code == 200:
            retrieve_data = retrieve_response.json()
            
            if retrieve_data.get("success"):
                print(f"Successfully retrieved file ({retrieve_data.get('file_size', 0)} bytes)")

                return {
                    "status": file_storage_response.get("status", "File retrieved successfully"),
                    "content": retrieve_data["content"],
                    "type": original_type,
                    "filename": filename,
                    "file_size": retrieve_data.get("file_size", 0)
                }
            else:
                print(f"Failed to retrieve file: {retrieve_data.get('error')}")
                return None
        else:
            print(f"File retrieval failed with status {retrieve_response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error retrieving stored file: {e}")
        return None

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
                            response = command_response["response"]
                            
                            if isinstance(response, dict) and response.get("type") == "file_storage":
                                print("Detected file storage response, retrieving file...")
                                file_result = retrieve_stored_file(base_url, response)
                                if file_result:
                                    return file_result
                                else:
                                    return {"error": "Failed to retrieve stored file"}
                            
                            return response
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
        
        if isinstance(result, dict):
            if 'content' in result:
                content_size = len(result.get('content', ''))
                print(f"Successfully retrieved content of size: {content_size} bytes")
            elif 'error' in result:
                print(f"Command completed with error: {result['error']}")
            else:
                print(f"Command completed successfully")
        
        if isinstance(result, dict) and command and 'get_file' in command:
            if 'content' in result:
                content = result['content']
                content_type = result.get('type', 'text')
                filename = result.get('filename', 'download')
                mimetype = result.get('mime_type')

                if not mimetype and filename:
                    import mimetypes
                    guessed_type, _ = mimetypes.guess_type(filename)
                    mimetype = guessed_type

                if content_type == 'binary':
                    try:
                        file_bytes = base64.b64decode(content)
                    except Exception:
                        file_bytes = content if isinstance(content, (bytes, bytearray)) else content.encode('utf-8', errors='replace')
                    file_stream = io.BytesIO(file_bytes)
                else:
                    file_stream = io.BytesIO(str(content).encode('utf-8'))

                file_stream.seek(0)
                return send_file(
                    file_stream,
                    mimetype=mimetype or ('text/plain' if content_type == 'text' else 'application/octet-stream'),
                    as_attachment=True,
                    download_name=filename
                )
            elif result.get('error'):
                return jsonify(result), 400
        
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