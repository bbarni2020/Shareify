# Cloud Command Execution API

## Overview

HTTP API for executing commands on connected Shareify servers through the cloud bridge.

## Base URL

```
https://command.bbarni.hackclub.app
```

## Endpoint

### Execute Command
- **URL**: `/`
- **Method**: `POST`
- **Content-Type**: `application/json`

## Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | No | Bearer JWT token for cloud bridge authentication |
| `X-Shareify-JWT` | No | Shareify JWT token for server-side authentication |
| `Content-Type` | Yes | Must be `application/json` |

## Request Body

All parameters are passed in the JSON request body.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `command` | string | Yes | - | API endpoint to execute |
| `method` | string | No | `GET` | HTTP method for the target server |
| `wait_time` | integer | No | `2` | Wait time between requests (seconds) |
| `body` | object | No | `{}` | Request body data for the target server |
| `jwt_token` | string | No | - | JWT token (alternative to Authorization header) |
| `shareify_jwt` | string | No | - | Shareify JWT token (alternative to X-Shareify-JWT header) |

## Request Examples

### Basic Command Execution
```bash
curl -X POST https://command.bbarni.hackclub.app/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Shareify-JWT: YOUR_SHAREIFY_JWT" \
  -H "Content-Type: application/json" \
  -d '{"command": "/user/get_self"}'
```

### With Custom Method and Wait Time
```bash
curl -X POST https://command.bbarni.hackclub.app/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Shareify-JWT: YOUR_SHAREIFY_JWT" \
  -H "Content-Type: application/json" \
  -d '{"command": "/resources", "method": "POST", "wait_time": 5}'
```

### With Request Body
```bash
curl -X POST https://command.bbarni.hackclub.app/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Shareify-JWT: YOUR_SHAREIFY_JWT" \
  -H "Content-Type: application/json" \
  -d '{"command": "/user/login", "method": "POST", "body": {"username": "admin", "password": "pass"}}'
```

### Using Token Parameters
```bash
curl -X POST https://command.bbarni.hackclub.app/ \
  -H "Content-Type: application/json" \
  -d '{"command": "/user/login", "method": "POST", "body": {"username": "admin", "password": "pass"}, "jwt_token": "YOUR_JWT_TOKEN", "shareify_jwt": "YOUR_SHAREIFY_JWT"}'
```

## Response Format

### Success Response

You will get back the called commmand response in simple JSON format.

### Error Response
```json
{
  "success": false,
  "error": "No command_ids returned",
  "timestamp": "2025-07-03 12:34:56"
}
```

## Available Commands

| Command | Method | Description |
|---------|--------|-------------|
| `/user/get_self` | GET | Get current user information |
| `/resources` | GET | List available resources |
| `/is_up` | GET | Check server status |
| `/user/login` | POST | Authenticate user |

## Authentication

### JWT Token
JWT token for cloud bridge authentication can be provided in two ways:
1. **Authorization Header**: `Bearer YOUR_JWT_TOKEN` (recommended)
2. **Request Body Parameter**: `jwt_token` field in JSON body

### Shareify JWT
Shareify JWT token for server-side authentication can be provided in two ways:
1. **X-Shareify-JWT Header**: `YOUR_SHAREIFY_JWT` (recommended)
2. **Request Body Parameter**: `shareify_jwt` field in JSON body

Headers take precedence over request body parameters when both are provided.

## Error Codes

| Status | Description |
|--------|-------------|
| 200 | Success |
| 500 | Server error or invalid parameters |

## Rate Limiting

No explicit rate limits applied. Reasonable usage expected.

## Examples

### Check Server Status
```bash
curl -X POST https://command.bbarni.hackclub.app/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Shareify-JWT: YOUR_SHAREIFY_JWT" \
  -H "Content-Type: application/json" \
  -d '{"command": "/is_up"}'
```

### Get User Information
```bash
curl -X POST https://command.bbarni.hackclub.app/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Shareify-JWT: YOUR_SHAREIFY_JWT" \
  -H "Content-Type: application/json" \
  -d '{"command": "/user/get_self"}'
```

### List Resources
```bash
curl -X POST https://command.bbarni.hackclub.app/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Shareify-JWT: YOUR_SHAREIFY_JWT" \
  -H "Content-Type: application/json" \
  -d '{"command": "/resources"}'
```

### Login with Body Data
```bash
curl -X POST https://command.bbarni.hackclub.app/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-Shareify-JWT: YOUR_SHAREIFY_JWT" \
  -H "Content-Type: application/json" \
  -d '{"command": "/user/login", "method": "POST", "body": {"username": "admin", "password": "pass"}}'
```
