# API Documentation

This document provides an overview of all the API endpoints available in the `main.py` file, including their parameters and responses.

**Authentication:** Most endpoints require JWT authentication via the `Authorization: Bearer <token>` header (except login, is_up, root, and static file endpoints). Tokens are obtained via the `/api/user/login` endpoint and are valid for 24 hours.

---

## General Endpoints

### `/api/is_up` [GET]
**Description:** Check if the server is running.  
**Authentication:** None required  
**Response:**
- `200 OK`: `{ "status": "Server is up" }`

---

### `/api/shutdown` [POST]
**Description:** Shutdown the system (requires admin privileges).  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `{ "status": "Shutting down" }`

---

### `/api/restart` [POST]
**Description:** Restart the system (requires admin privileges).  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `{ "status": "Restarting" }`

---

## File Management Endpoints

### `/api/finder` [GET]
**Description:** List files and directories at a given path.  
**Authentication:** JWT token required  
**Parameters:**
- `path` (query, optional): The directory path to list. If not provided, lists root directory.  
**Response:**
- `200 OK`: `{ "items": [...] }` - Array of file/directory names
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/new_file` [POST]
**Description:** Create a new file.  
**Authentication:** JWT token required  
**Request Body:**
- `file_name` (string): Name of the file.
- `path` (string, optional): Directory path.
- `file_content` (string): Content of the file.  
**Response:**
- `200 OK`: `{ "status": "File created", "path": "..." }`
- `400 Bad Request`: `{ "error": "No file name or content provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/delete_file` [POST]
**Description:** Delete a file.  
**Authentication:** JWT token required  
**Request Body:**
- `path` (string): Path of the file to delete.  
**Response:**
- `200 OK`: `{ "status": "File deleted" }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `400 Bad Request`: `{ "error": "No path provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/edit_file` [POST]
**Description:** Edit a file's content.  
**Authentication:** JWT token required  
**Request Body:**
- `path` (string): Path of the file to edit.
- `file_content` (string, optional): New content for the file. Defaults to empty string if not provided.  
**Response:**
- `200 OK`: `{ "status": "File edited", "path": "..." }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `400 Bad Request`: `{ "error": "No path provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/get_file` [GET]
**Description:** Retrieve the content of a file.  
**Authentication:** JWT token required  
**Request Body:**
- `file_path` (string): Path of the file to retrieve.  
**Response:**
- `200 OK`: `{ "status": "File content retrieved", "content": "..." }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `400 Bad Request`: `{ "error": "No file path provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`
**Note:** Binary files (images, videos) are encoded in latin1 format.

---

### `/api/rename_file` [GET]
**Description:** Rename a file.  
**Authentication:** JWT token required  
**Request Body:**
- `file_name` (string): Current name of the file.
- `new_name` (string): New name for the file.
- `path` (string): Directory path.  
**Response:**
- `200 OK`: `{ "status": "File renamed", "path": "..." }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `400 Bad Request`: `{ "error": "No file name provided" }` or `{ "error": "No path provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/upload` [POST]
**Description:** Upload a file.  
**Authentication:** JWT token required  
**Request Body (multipart/form-data):**
- `file` (file): The file to upload.
- `path` (string, optional): Directory path to upload to. Defaults to root if not provided.  
**Response:**
- `200 OK`: `{ "status": "File uploaded" }`
- `400 Bad Request`: `{ "error": "No file provided" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/download` [GET]
**Description:** Download a file or folder (as zip).  
**Authentication:** JWT token required  
**Parameters:**
- `file_path` (query): Path of the file/folder to download.  
**Response:**
- `200 OK`: File download or zip download for folders
- `400 Bad Request`: `{ "error": "No file path provided" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `404 Not Found`: `{ "error": "File or folder does not exist" }`
- `500 Internal Server Error`: `{ "error": "Failed to create zip: ..." }` (for folders)

---

## Folder Management Endpoints

### `/api/create_folder` [POST]
**Description:** Create a new folder.  
**Authentication:** JWT token required  
**Request Body:**
- `folder_name` (string): Name of the folder.
- `path` (string, optional): Directory path.  
**Response:**
- `200 OK`: `{ "status": "Folder created", "path": "..." }`
- `400 Bad Request`: `{ "error": "No folder name provided" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/delete_folder` [POST]
**Description:** Delete a folder.  
**Authentication:** JWT token required  
**Request Body:**
- `path` (string): Path of the folder to delete.  
**Response:**
- `200 OK`: `{ "status": "Folder deleted" }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `400 Bad Request`: `{ "error": "No path provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/rename_folder` [POST]
**Description:** Rename a folder.  
**Authentication:** JWT token required  
**Request Body:**
- `folder_name` (string): Current name of the folder.
- `new_name` (string): New name for the folder.
- `path` (string, optional): Directory path. If not provided, operates in root directory.  
**Response:**
- `200 OK`: `{ "status": "Folder renamed", "path": "..." }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `400 Bad Request`: `{ "error": "No folder name provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

## Command Execution Endpoints

### `/api/command` [POST]
**Description:** Execute a system command.  
**Authentication:** JWT token required  
**Request Body:**
- `command` (string): Command to execute.  
**Response:**
- `200 OK`: `{ "status": "Command executed", "output": "..." }`
- `400 Bad Request`: `{ "error": "No command provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

## System Information Endpoints

### `/api/resources` [GET]
**Description:** Get system resource usage (CPU, memory, disk).  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `{ "cpu": number, "memory": number, "disk": number }` - All values as percentages (integers)
- `500 Internal Server Error`: `{ "error": "..." }`

---

## User Management Endpoints

### `/api/user/create` [POST]
**Description:** Create a new user.  
**Authentication:** JWT token required  
**Request Body:**
- `username` (string): Username.
- `password` (string): Password.
- `name` (string): Full name.
- `role` (string): User role.
- `paths` (string, optional): Accessible paths (JSON format).
- `paths_write` (string, optional): Writable paths (JSON format).  
**Response:**
- `200 OK`: `{ "status": "User created", "API_KEY": "..." }`
- `400 Bad Request`: `{ "error": "No username, password, name or role provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/user/delete` [POST]
**Description:** Delete a user and automatically remove their role from the roles configuration.  
**Authentication:** JWT token required  
**Request Body:**
- `username` (string): Username to delete.  
**Response:**
- `200 OK`: `{ "status": "User deleted" }`
- `400 Bad Request`: `{ "error": "No username provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

**Note:** When a user is deleted, their role will be automatically removed from all endpoints in the roles configuration file (except for admin roles).

---

### `/api/user/edit` [POST]
**Description:** Edit a user's details.  
**Authentication:** JWT token required  
**Request Body:**
- `username` (string): Username.
- `password` (string): Password.
- `name` (string): Full name.
- `role` (string): User role.
- `paths` (string): Accessible paths.
- `paths_write` (string): Writable paths.  
- `id` (string): User ID.
**Response:**
- `200 OK`: `{ "status": "User edited" }`
- `400 Bad Request`: `{ "error": "No username, password, name, role or paths provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/user/login` [POST]
**Description:** Login a user and receive a JWT token.  
**Authentication:** None required  
**Request Body:**
- `username` (string): Username.
- `password` (string): Password.  
**Response:**
- `200 OK`: `{ "token": "..." }` - JWT token valid for 24 hours
- `401 Unauthorized`: `{ "error": "Invalid username or password" }`
- `400 Bad Request`: `{ "error": "No username or password provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

**Note:** The returned JWT token should be used in the `Authorization: Bearer <token>` header for subsequent API calls.

---

### `/api/user/get_self` [GET]
**Description:** Retrieve the current user's details.  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `{ "username": "...", "password": "...", "name": "...", "role": "...", "ftp_users": "...", "paths": "...", "settings": "...", "paths_write": "..." }`
- `404 Not Found`: `{ "error": "User not found" }`

---

### `/api/user/get_all` [GET]
**Description:** Retrieve all users.  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `[ { "username": "...", "password": "...", "name": "...", "ip": "...", "role": "...", "ftp_users": "...", "paths": "...", "settings": "...", "API_KEY": "...", "paths_write": "..." }, ... ]`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/user/edit_self` [POST]
**Description:** Edit the current user's details.  
**Authentication:** JWT token required  
**Request Body:** JSON object with optional fields to update:
- `username` (string, optional): New username.
- `password` (string, optional): New password.
- `name` (string, optional): New full name.
- `ftp_users` (string, optional): FTP users.
- `settings` (string, optional): User settings.
- `API_KEY` (string, optional): New API key.  
**Response:**
- `200 OK`: `{ "status": "User updated" }`
- `400 Bad Request`: `{ "error": "No valid fields provided for update" }`
- `404 Not Found`: `{ "error": "User not found" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

## FTP Management Endpoints

### `/api/ftp/create_user` [POST]
**Description:** Create an FTP user.  
**Authentication:** JWT token required  
**Request Body:**
- `username` (string): FTP username.
- `password` (string): FTP password.
- `path` (string, optional): FTP home directory. If not provided, uses server's default path.
- `permissions` (string): FTP permissions.  
**Response:**
- `200 OK`: `{ "status": "FTP user created" }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `400 Bad Request`: `{ "error": "No username, password or permissions provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/ftp/delete_user` [POST]
**Description:** Delete an FTP user.  
**Authentication:** JWT token required  
**Request Body:**
- `username` (string): FTP username to delete.  
**Response:**
- `200 OK`: `{ "status": "FTP user deleted" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/ftp/get_users` [GET]
**Description:** Retrieve all FTP users.  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `[ { "username": "...", "password": "...", "path": "...", "permissions": "..." }, ... ]`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/ftp/edit_user` [POST]
**Description:** Edit an FTP user's details.  
**Authentication:** JWT token required  
**Request Body:**
- `username` (string): FTP username.
- `password` (string, optional): New password.
- `path` (string, optional): New home directory.
- `permissions` (string, optional): New permissions.  
**Response:**
- `200 OK`: `{ "status": "FTP user edited" }`
- `404 Not Found`: `{ "error": "User not found" }` or `{ "error": "Path does not exist" }`
- `400 Bad Request`: `{ "error": "No username provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/ftp/start` [POST]
**Description:** Start the FTP server.  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `{ "status": "FTP server started" }`
- `500 Internal Server Error`: `{ "error": "..." }`
**Note:** Also updates the settings file to set FTP to enabled.

---

### `/api/ftp/stop` [POST]
**Description:** Stop the FTP server.  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `{ "status": "FTP server stopped" }`
- `400 Bad Request`: `{ "error": "FTP server is not running" }`
- `500 Internal Server Error`: `{ "error": "..." }`

---

## Server Management Endpoints

### `/api/get_logs` [GET]
**Description:** Retrieve server logs.  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `[ { "id": number, "timestamp": "...", "action": "...", "ip": "..." }, ... ]` - Logs ordered by ID descending (newest first)

---

### `/api/get_settings` [GET]
**Description:** Retrieve server settings.  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `{ ...settings... }` - Complete settings object from settings.json
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/update_settings` [POST]
**Description:** Update server settings.  
**Authentication:** JWT token required  
**Request Body:** JSON object with updated settings.  
**Response:**
- `200 OK`: `{ "status": "Settings updated" }`
- `400 Bad Request`: `{ "error": "No settings provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`
**Note:** This endpoint reloads the JSON configuration files after updating.

---

### `/api/get_version` [GET]
**Description:** Get the server version.  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `{ "version": "..." }`

---

### `/api/update` [POST]
**Description:** Trigger a server update (runs update.py in background).  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `{ "status": "Update started" }`

---

### `/update_start_exit_program` [POST]
**Description:** Exit program for update process (calls stop_completely()).  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `{ "status": "Update started" }`

---

### `/api/role/get` [GET]
**Description:** Retrieve all roles from roles.json.  
**Authentication:** JWT token required  
**Response:**
- `200 OK`: `{ ...roles... }` - Complete roles object from roles.json
- `500 Internal Server Error`: `{ "error": "..." }`

---

### `/api/role/edit` [POST]
**Description:** Edit roles configuration.  
**Authentication:** JWT token required  
**Request Body:** JSON object with updated roles.  
**Response:**
- `200 OK`: `{ "status": "Roles updated" }`
- `400 Bad Request`: `{ "error": "No roles provided" }`
- `500 Internal Server Error`: `{ "error": "..." }`
**Note:** This endpoint reloads the JSON configuration files after updating.

---

## Static File Serving

### `/` [GET]
**Description:** Serve the main index.html page.  
**Authentication:** None required

---

### `/auth` [GET]
**Description:** Serve the login.html page.  
**Authentication:** None required

---

### `/web/<path:filename>` [GET]
**Description:** Serve static files from the web directory.  
**Authentication:** None required  
**Parameters:**
- `filename` (path): The filename/path of the static file to serve.

---

### `/web/assets/<path:filename>` [GET]
**Description:** Serve asset files from the web/assets directory.  
**Authentication:** None required  
**Parameters:**
- `filename` (path): The filename/path of the asset file to serve.
**Note:** Automatically detects and sets appropriate MIME types.

---

## JWT Authentication

The API uses JSON Web Tokens (JWT) for authentication. Here's how it works:

### Getting a Token
1. Send a POST request to `/api/user/login` with username and password
2. Receive a JWT token that's valid for 24 hours
3. Use this token in the `Authorization: Bearer <token>` header for all subsequent requests

### Token Structure
- **Algorithm:** HS256
- **Expiration:** 24 hours from issuance
- **Payload includes:** user_id, username, exp (expiration time)

### Using the Token
Include the token in the Authorization header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Validation
The server validates tokens before processing requests:
- Checks token signature and expiration
- Verifies user still exists in database
- Loads user role and permissions

### Error Handling
- **Missing token:** Returns 401 with "Unauthorized"
- **Expired token:** Returns 401 with "Token expired" 
- **Invalid token:** Returns 401 with "Invalid token"
- **User not found:** Returns 401 with "Unauthorized"

### Migration Notes
- The system has migrated from API key authentication to JWT tokens
- API keys are still stored in the user database for potential future use
- All endpoints now require JWT authentication instead of `X-API-KEY` headers

---

## Access Control

The API implements a JWT-based role access control system:

1. **Authentication:** Most endpoints require JWT authentication via `Authorization: Bearer <token>` header
2. **Path Access Control:** Users have specific read/write permissions for different paths
3. **Role-based Permissions:** Different endpoints are accessible based on user roles defined in `roles.json`
4. **Token Expiration:** JWT tokens are valid for 24 hours and must be refreshed via login

### Access Functions:
- `has_access(path)`: Checks if user can read from a specific path
- `has_write_access(path)`: Checks if user can write to a specific path  
- `is_accessible(address)`: Checks if user role can access a specific endpoint

### JWT Token Errors:
- `401 Unauthorized` with `{"error": "Token expired"}`: Token has expired, re-login required
- `401 Unauthorized` with `{"error": "Invalid token"}`: Token is malformed or invalid
- `401 Unauthorized` with `{"error": "Unauthorized"}`: Missing token or user not found

---

## Database Schema

### Users Table:
- `id` (INTEGER PRIMARY KEY)
- `username` (TEXT, UNIQUE)
- `password` (TEXT)
- `name` (TEXT)
- `ip` (TEXT)
- `role` (TEXT)
- `ftp_users` (TEXT)
- `paths` (TEXT) - JSON string of accessible paths
- `settings` (TEXT) - User-specific settings
- `API_KEY` (TEXT, UNIQUE)
- `paths_write` (TEXT) - JSON string of writable paths

### Logs Table:
- `id` (INTEGER PRIMARY KEY)
- `timestamp` (TEXT)
- `action` (TEXT)
- `ip` (TEXT)

---

## Error Handling

All endpoints return consistent error responses:
- `400 Bad Request`: Missing required parameters or invalid input
- `401 Unauthorized`: Invalid or missing API key, or insufficient permissions
- `404 Not Found`: Requested resource doesn't exist
- `500 Internal Server Error`: Server-side errors with error details

---

For more details, refer to the source code in `main.py`.

---

### GET `/api/role/self`

**Description:** Get the current user's role permissions for all endpoints

**Headers:**
- `Authorization: Bearer <token>`: JWT token (required)

**Response:**
- **200 OK**: Returns permissions object with endpoint access status
  ```json
  {
    "/api/command": true,
    "/api/finder": true,
    "/api/create_folder": false,
    "/api/delete_file": false,
    "/api/user/create": true
  }
  ```

- **404 Not Found**: Role not found
  ```json
  {
    "error": "Role not found"
  }
  ```

- **500 Internal Server Error**: Server error
  ```json
  {
    "error": "Error message"
  }
  ```

**Notes:**
- Returns a boolean value for each endpoint indicating whether the user's role has access
- `true` means the user can access the endpoint
- `false` means the user cannot access the endpoint
- Only includes endpoints that exist in the roles configuration