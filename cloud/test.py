import requests
import time

base_url = "http://127.0.0.1:5698"

def cloud():
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYmFlMzljMDUtZWRlNi00MDJjLWExZDEtYTdjYTJhMzJhMjJhIiwiand0X2lkIjoiNTI1ZjM2NDUtYjQ1Yi00MmE1LWI3ODgtZjAwMDRmZjBhMDFkIiwiZXhwIjoxNzUxMzcyMzQ3LCJpYXQiOjE3NTEyODU5NDd9.KY3lBSnjJ8dKV6H6BRPRAn0Hj1yrz4QHEVflDvZ6nTE"
    command = "/user/get_self"
    method = "GET"
    body = {}
    shareify_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxNzUxMzcyODkyfQ.oozf0-bthJtA1JlvHmSgB30X7Jx7GwRdybsfCom8l7Q"

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

    r = requests.post(f"{base_url}/cloud/command", json=payload, headers=headers)
    command_ids = r.json().get("command_ids", [])
    if not command_ids:
        print("No command_ids returned")
        exit(1)
    time.sleep(2)
    params = [("command_id", cid) for cid in command_ids]
    params.append(("jwt_token", jwt_token))
    r2 = requests.get(f"{base_url}/cloud/response", headers=headers, params=params)
    response_data = r2.json()
    for command_id, command_response in response_data.get("responses", {}).items():
        if "response" in command_response:
            print(command_response["response"])
        else:
            print(command_response)


cloud()