# API Documentation

This document provides an overview of all the API endpoints available in the `main.py` file, including their parameters and responses.

---

## General Endpoints

### `/api/is_up` [GET]
**Description:** Check if the server is running.  
**Response:**
- `200 OK`: `{ "status": "Server is up" }`

---

### `/api/shutdown` [POST]
**Description:** Shutdown the server.  
**Response:**
- `200 OK`: `{ "status": "Shutting down" }`

---

### `/api/restart` [POST]
**Description:** Restart the server.  
**Response:**
- `200 OK`: `{ "status": "Restarting" }`

---

## File Management Endpoints

### `/api/finder` [GET]
**Description:** List files and directories at a given path.  
**Parameters:**
- `path` (query): The directory path to list.  
**Response:**
- `200 OK`: `{ "items": [...] }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`

---

### `/api/new_file` [POST]
**Description:** Create a new file.  
**Request Body:**
- `file_name` (string): Name of the file.
- `path` (string, optional): Directory path.
- `file_content` (string): Content of the file.  
**Response:**
- `200 OK`: `{ "status": "File created", "path": "..." }`
- `400 Bad Request`: `{ "error": "No file name or content provided" }`

---

### `/api/delete_file` [POST]
**Description:** Delete a file.  
**Request Body:**
- `path` (string): Path of the file to delete.  
**Response:**
- `200 OK`: `{ "status": "File deleted" }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`

---

### `/api/edit_file` [POST]
**Description:** Edit a file's content.  
**Request Body:**
- `path` (string): Path of the file to edit.
- `file_content` (string): New content for the file.  
**Response:**
- `200 OK`: `{ "status": "File edited", "path": "..." }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`

---

### `/api/get_file` [GET]
**Description:** Retrieve the content of a file.  
**Request Body:**
- `file_path` (string): Path of the file to retrieve.  
**Response:**
- `200 OK`: `{ "status": "File content retrieved", "content": "..." }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `400 Bad Request`: `{ "error": "No file path provided" }`

---

### `/api/rename_file` [GET]
**Description:** Rename a file.  
**Request Body:**
- `file_name` (string): Current name of the file.
- `new_name` (string): New name for the file.
- `path` (string): Directory path.  
**Response:**
- `200 OK`: `{ "status": "File renamed", "path": "..." }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `400 Bad Request`: `{ "error": "No file name provided" }`

---

### `/api/upload` [POST]
**Description:** Upload a file.  
**Request Body (multipart/form-data):**
- `file` (file): The file to upload.
- `path` (string, optional): Directory path to upload to.  
**Response:**
- `200 OK`: `{ "status": "File uploaded" }`
- `400 Bad Request`: `{ "error": "No file provided" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`

---

### `/api/download` [GET]
**Description:** Download a file or folder (as zip).  
**Parameters:**
- `file_path` (query): Path of the file/folder to download.  
**Response:**
- `200 OK`: File download or zip download for folders
- `400 Bad Request`: `{ "error": "No file path provided" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `404 Not Found`: `{ "error": "File or folder does not exist" }`

---

## Folder Management Endpoints

### `/api/create_folder` [POST]
**Description:** Create a new folder.  
**Request Body:**
- `folder_name` (string): Name of the folder.
- `path` (string, optional): Directory path.  
**Response:**
- `200 OK`: `{ "status": "Folder created", "path": "..." }`
- `400 Bad Request`: `{ "error": "No folder name provided" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`

---

### `/api/delete_folder` [POST]
**Description:** Delete a folder.  
**Request Body:**
- `path` (string): Path of the folder to delete.  
**Response:**
- `200 OK`: `{ "status": "Folder deleted" }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `400 Bad Request`: `{ "error": "No path provided" }`

---

### `/api/rename_folder` [POST]
**Description:** Rename a folder.  
**Request Body:**
- `folder_name` (string): Current name of the folder.
- `new_name` (string): New name for the folder.
- `path` (string): Directory path.  
**Response:**
- `200 OK`: `{ "status": "Folder renamed", "path": "..." }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`
- `400 Bad Request`: `{ "error": "No folder name provided" }`

---

## Command Execution Endpoints

### `/api/command` [POST]
**Description:** Execute a system command.  
**Request Body:**
- `command` (string): Command to execute.  
**Response:**
- `200 OK`: `{ "status": "Command executed", "output": "..." }`
- `400 Bad Request`: `{ "error": "No command provided" }`

---

## User Management Endpoints

### `/api/user/create` [POST]
**Description:** Create a new user.  
**Request Body:**
- `username` (string): Username.
- `password` (string): Password.
- `name` (string): Full name.
- `role` (string): User role.
- `paths` (string, optional): Accessible paths.
- `paths_write` (string, optional): Writable paths.  
**Response:**
- `200 OK`: `{ "status": "User created", "API_KEY": "..." }`
- `400 Bad Request`: `{ "error": "No username, password, name or role provided" }`

---

### `/api/user/delete` [POST]
**Description:** Delete a user.  
**Request Body:**
- `username` (string): Username to delete.  
**Response:**
- `200 OK`: `{ "status": "User deleted" }`
- `400 Bad Request`: `{ "error": "No username provided" }`

---

### `/api/user/edit` [GET]
**Description:** Edit a user's details.  
**Request Body:**
- `username` (string): Username.
- `password` (string): Password.
- `name` (string): Full name.
- `role` (string): User role.
- `paths` (string): Accessible paths.
- `id` (string): User ID.  
**Response:**
- `200 OK`: `{ "status": "User edited" }`
- `400 Bad Request`: `{ "error": "No username, password, name, role or paths provided" }`

---

### `/api/user/login` [POST]
**Description:** Login a user.  
**Request Body:**
- `username` (string): Username.
- `password` (string): Password.  
**Response:**
- `200 OK`: `{ "API_KEY": "..." }`
- `401 Unauthorized`: `{ "error": "Invalid username or password" }`
- `400 Bad Request`: `{ "error": "No username or password provided" }`

---

### `/api/user/get_self` [GET]
**Description:** Retrieve the current user's details.  
**Response:**
- `200 OK`: `{ "username": "...", "password": "...", "name": "...", "role": "...", "ftp_users": "...", "paths": "...", "settings": "...", "paths_write": "..." }`
- `404 Not Found`: `{ "error": "User not found" }`

---

### `/api/user/get_all` [GET]
**Description:** Retrieve all users.  
**Response:**
- `200 OK`: `[ { "username": "...", "password": "...", "name": "...", "ip": "...", "role": "...", "ftp_users": "...", "paths": "...", "settings": "...", "API_KEY": "...", "paths_write": "..." }, ... ]`

---

### `/api/user/edit_self` [POST]
**Description:** Edit the current user's details.  
**Request Body:** JSON object with fields to update:
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

---

## FTP Management Endpoints

### `/api/ftp/create_user` [POST]
**Description:** Create an FTP user.  
**Request Body:**
- `username` (string): FTP username.
- `password` (string): FTP password.
- `path` (string, optional): FTP home directory.
- `permissions` (string): FTP permissions.  
**Response:**
- `200 OK`: `{ "status": "FTP user created" }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `400 Bad Request`: `{ "error": "No username, password or permissions provided" }`

---

### `/api/ftp/delete_user` [POST]
**Description:** Delete an FTP user.  
**Request Body:**
- `username` (string): FTP username to delete.  
**Response:**
- `200 OK`: `{ "status": "FTP user deleted" }`

---

### `/api/ftp/get_users` [GET]
**Description:** Retrieve all FTP users.  
**Response:**
- `200 OK`: `[ { "username": "...", "password": "...", "path": "...", "permissions": "..." }, ... ]`

---

### `/api/ftp/edit_user` [POST]
**Description:** Edit an FTP user's details.  
**Request Body:**
- `username` (string): FTP username.
- `password` (string, optional): New password.
- `path` (string, optional): New home directory.
- `permissions` (string, optional): New permissions.  
**Response:**
- `200 OK`: `{ "status": "FTP user edited" }`
- `404 Not Found`: `{ "error": "User not found" }` or `{ "error": "Path does not exist" }`
- `400 Bad Request`: `{ "error": "No username provided" }`

---

### `/api/ftp/start` [POST]
**Description:** Start the FTP server.  
**Response:**
- `200 OK`: `{ "status": "FTP server started" }`

---

### `/api/ftp/stop` [POST]
**Description:** Stop the FTP server.  
**Response:**
- `200 OK`: `{ "status": "FTP server stopped" }`
- `400 Bad Request`: `{ "error": "FTP server is not running" }`

---

## System Information Endpoints

### `/api/resources` [GET]
**Description:** Get system resource usage.  
**Response:**
- `200 OK`: `{ "cpu": ..., "memory": ..., "disk": ... }`

---

### `/api/get_logs` [GET]
**Description:** Retrieve server logs.  
**Response:**
- `200 OK`: `[ { "id": ..., "timestamp": ..., "action": ..., "ip": ... }, ... ]`

---

### `/api/get_settings` [GET]
**Description:** Retrieve server settings.  
**Response:**
- `200 OK`: `{ ...settings... }`

---

### `/api/update_settings` [POST]
**Description:** Update server settings.  
**Request Body:** JSON object with updated settings.  
**Response:**
- `200 OK`: `{ "status": "Settings updated" }`
- `400 Bad Request`: `{ "error": "No settings provided" }`

---

### `/api/get_version` [GET]
**Description:** Get the server version.  
**Response:**
- `200 OK`: `{ "version": "..." }`

---

### `/api/update` [POST]
**Description:** Trigger a server update.  
**Response:**
- `200 OK`: `{ "status": "Update started" }`

---

### `/update_start_exit_program` [POST]
**Description:** Exit program for update process.  
**Response:**
- `200 OK`: `{ "status": "Update started" }`

---

### `/api/role/get` [GET]
**Description:** Retrieve all roles.  
**Response:**
- `200 OK`: `{ ...roles... }`

---

### `/api/role/edit` [POST]
**Description:** Edit roles.  
**Request Body:** JSON object with updated roles.  
**Response:**
- `200 OK`: `{ "status": "Roles updated" }`
- `400 Bad Request`: `{ "error": "No roles provided" }`

---

## Static File Serving

### `/` [GET]
**Description:** Serve the main index.html page.

---

### `/auth` [GET]
**Description:** Serve the login.html page.

---

### `/web/<path:filename>` [GET]
**Description:** Serve static files from the web directory.

---

### `/web/assets/<path:filename>` [GET]
**Description:** Serve asset files from the web/assets directory.

---

For more details, refer to the source code in `main.py`.