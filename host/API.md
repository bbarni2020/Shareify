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

---

### `/api/edit_file` [POST]
**Description:** Edit a file's content.  
**Request Body:**
- `path` (string): Path of the file to edit.
- `file_content` (string): New content for the file.  
**Response:**
- `200 OK`: `{ "status": "File edited", "path": "..." }`

---

### `/api/get_file` [GET]
**Description:** Retrieve the content of a file.  
**Request Body:**
- `file_path` (string): Path of the file to retrieve.  
**Response:**
- `200 OK`: `{ "status": "File content retrieved", "content": "..." }`
- `404 Not Found`: `{ "error": "Path does not exist" }`
- `401 Unauthorized`: `{ "error": "Unauthorized" }`

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

---

### `/api/delete_folder` [POST]
**Description:** Delete a folder.  
**Request Body:**
- `path` (string): Path of the folder to delete.  
**Response:**
- `200 OK`: `{ "status": "Folder deleted" }`
- `404 Not Found`: `{ "error": "Path does not exist" }`

---

### `/api/rename_folder` [POST]
**Description:** Rename a folder.  
**Request Body:**
- `folder_name` (string): Current name of the folder.
- `new_name` (string): New name for the folder.
- `path` (string): Directory path.  
**Response:**
- `200 OK`: `{ "status": "Folder renamed", "path": "..." }`

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
**Response:**
- `200 OK`: `{ "status": "User created" }`
- `400 Bad Request`: `{ "error": "No username, password, name or role provided" }`

---

### `/api/user/delete` [POST]
**Description:** Delete a user.  
**Request Body:**
- `username` (string): Username to delete.  
**Response:**
- `200 OK`: `{ "status": "User deleted" }`
- `404 Not Found`: `{ "error": "User not found" }`

---

### `/api/user/login` [POST]
**Description:** Login a user.  
**Request Body:**
- `username` (string): Username.
- `password` (string): Password.  
**Response:**
- `200 OK`: `{ "API_KEY": "..." }`
- `401 Unauthorized`: `{ "error": "Invalid username or password" }`

---

### `/api/user/get_self` [GET]
**Description:** Retrieve the current user's details.  
**Response:**
- `200 OK`: `{ ...user details... }`
- `404 Not Found`: `{ "error": "User not found" }`

---

### `/api/user/get_all` [GET]
**Description:** Retrieve all users.  
**Response:**
- `200 OK`: `[ { ...user details... }, ... ]`

---

### `/api/user/edit_self` [POST]
**Description:** Edit the current user's details.  
**Request Body:** JSON object with fields to update.  
**Response:**
- `200 OK`: `{ "status": "User updated" }`
- `400 Bad Request`: `{ "error": "No valid fields provided for update" }`

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
- `404 Not Found`: `{ "error": "User not found" }`

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

For more details, refer to the source code in `main.py`.