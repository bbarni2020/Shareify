import requests
import time
import os

base_url = "http://127.0.0.1:5698"

def cloud_full():
    print("Starting cloud_full function")
    jwt_token = os.getenv('JWT_TOKEN', '')
    command = "/user/get_self"
    method = "GET"
    body = {}
    shareify_jwt = os.getenv('SHAREIFY_JWT', '')

    if not jwt_token:
        print("JWT_TOKEN environment variable is required")
        exit(1)
    
    if not shareify_jwt:
        print("SHAREIFY_JWT environment variable is required")
        exit(1)

    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }
    
    if shareify_jwt:
        headers["X-Shareify-JWT"] = shareify_jwt
    
    headers["Content-Type"] = "application/json"

    payload = {
        "command": command,
        "method": method,
        "body": body
    }

    print(f"Sending command: {command} with method: {method} and body: {body}")
    r = requests.post(f"{base_url}/cloud/command", json=payload, headers=headers)
    command_ids = r.json().get("command_ids", [])
    if not command_ids:
        print("No command_ids returned")
        exit(1)
    time.sleep(2)
    print(f"Command IDs: {command_ids}")
    params = [("command_id", cid) for cid in command_ids]
    params.append(("jwt_token", jwt_token))
    r2 = requests.get(f"{base_url}/cloud/response", headers=headers, params=params)
    response_data = r2.json()
    print(f"Response data: {response_data}")
    for command_id, command_response in response_data.get("responses", {}).items():
        if "response" in command_response:
            return (command_response["response"])
        else:
            return (command_response)

if __name__ == '__main__':
    result = cloud_full()
    print(f"Final result: {result}")