# Shareify API Reference

This is the API docs for the main server. I tried to keep the endpoints logical, but some of them are a bit weird because I added features as I needed them.

**Auth stuff:** Most endpoints need a JWT token in the `Authorization: Bearer <token>` header. Get one by hitting `/api/user/login` first. Tokens last 24 hours, then you need to login again.

## Basic endpoints

### `GET /api/is_up`
Check if the server's running. Rate limited to 1 req/sec.
- No auth needed
- Returns: `{ "status": "Server is up" }`

### `POST /api/shutdown`
Shuts down the system. Admin only.
- JWT required
- Returns: `{ "status": "Shutting down" }`

### `POST /api/restart` 
Restarts the system. Admin only.
- JWT required  
- Returns: `{ "status": "Restarting" }`

## File stuff

### `GET /api/finder`
Lists files and folders in a directory.
- JWT required
- Query param `path` (optional) - defaults to root
- Returns: `{ "items": [...] }` or `404` if path doesn't exist

### `POST /api/new_file`
Creates a new file.
- JWT required
- Body: `file_name`, `file_content`, `path` (optional)
- Returns: `{ "status": "File created", "path": "..." }` 
- `400` if missing name or content

### `POST /api/delete_file`
Deletes a file.
- JWT required
- Body: `path`
- Returns: `{ "status": "File deleted" }` or `404` if file doesn't exist

### `POST /api/edit_file`
Edit file content.
- JWT required
- Body: `path`, `file_content` (optional, defaults to empty)
- Returns: `{ "status": "File edited", "path": "..." }`

### `GET /api/get_file`
Get file content. Handles text and binary files differently.
- JWT required
- Query param: `file_path`
- Returns: 
  - Text files: `{ "status": "File content retrieved", "content": "...", "type": "text" }`
  - Binary files: `{ "status": "File content retrieved", "content": "...", "type": "binary" }` (base64 encoded)

### `POST /api/rename_file`
Rename a file.
- JWT required
- Body: `file_name`, `new_name`, `path`
- Returns: `{ "status": "File renamed", "path": "..." }`

### `POST /api/upload`
Upload files via multipart form.
- JWT required
- Form data: `file`, `path` (optional)
- Returns: `{ "status": "File uploaded" }`

### `GET /api/download`
Download files or folders (folders become zip files).
- JWT required
- Query param: `file_path`
- Returns: File download or zip for folders

## Folder operations

### `POST /api/create_folder`
Makes a new folder.
- JWT required
- Body: `folder_name`, `path` (optional)
- Returns: `{ "status": "Folder created", "path": "..." }`

### `POST /api/delete_folder`
Deletes a folder.
- JWT required
- Body: `path`
- Returns: `{ "status": "Folder deleted" }` or `404` if doesn't exist

### `POST /api/rename_folder`
Renames a folder.
- JWT required
- Body: `folder_name`, `new_name`, `path` (optional, defaults to root)
- Returns: `{ "status": "Folder renamed", "path": "..." }`

## Command execution

### `POST /api/command`
Run system commands. Be careful with this one.
- JWT required
- Body: `command`
- Returns: `{ "status": "Command executed", "output": "..." }`

## System info

### `GET /api/resources`
Get CPU, memory, disk usage as percentages.
- JWT required
- Returns: `{ "cpu": 45, "memory": 67, "disk": 23 }`

## User management

### `POST /api/user/create`
Create a new user.
- JWT required
- Body: `username`, `password`, `name`, `role`, `paths` (optional JSON), `paths_write` (optional JSON)
- Returns: `{ "status": "User created", "API_KEY": "..." }`

### `POST /api/user/delete`
Delete a user. Also removes their role from the config automatically.
- JWT required
- Body: `username`
- Returns: `{ "status": "User deleted" }`

### `POST /api/user/edit`
Edit user details.
- JWT required
- Body: `username`, `name`, `paths`, `paths_write`, `id`, `password` (optional)
- Returns: `{ "status": "User edited" }`

### `POST /api/user/login`
Login and get a JWT token. Rate limited to 1 req/sec.
- No auth needed
- Body: `username`, `password`
- Returns: `{ "token": "..." }` (valid for 24 hours)
- `401` for wrong credentials

### `GET /api/user/get_self`
Get your own user info.
- JWT required
- Returns all your user data

### `GET /api/user/get_all`
Get all users (probably admin only).
- JWT required
- Returns array of all users

### `POST /api/user/edit_self`
Edit your own profile.
- JWT required
- Body: any user fields you want to update (all optional)
- Returns: `{ "status": "User updated" }`

## FTP management

### `POST /api/ftp/create_user`
Create FTP user.
- JWT required
- Body: `username`, `password`, `permissions`, `path` (optional)
- Returns: `{ "status": "FTP user created" }`

### `POST /api/ftp/delete_user`
Delete FTP user.
- JWT required
- Body: `username`
- Returns: `{ "status": "FTP user deleted" }`

### `GET /api/ftp/get_users`
List all FTP users.
- JWT required
- Returns array of FTP users

### `POST /api/ftp/edit_user`
Edit FTP user.
- JWT required
- Body: `username`, `password` (optional), `path` (optional), `permissions` (optional)
- Returns: `{ "status": "FTP user edited" }`

### `POST /api/ftp/start`
Start the FTP server.
- JWT required
- Returns: `{ "status": "FTP server started" }`

### `POST /api/ftp/stop`
Stop the FTP server.
- JWT required
- Returns: `{ "status": "FTP server stopped" }`

## Server management

### `GET /api/get_logs`
Get server logs, newest first.
- JWT required
- Returns array of log entries with id, timestamp, action, ip

### `GET /api/get_settings`
Get current server settings.
- JWT required
- Returns the entire settings.json object

### `POST /api/update_settings`
Update server settings.
- JWT required
- Body: JSON object with new settings
- Returns: `{ "status": "Settings updated" }`
- Automatically preserves the `com_password` field

### `GET /api/get_version`
Get server version.
- JWT required
- Returns: `{ "version": "..." }`

### `POST /api/update`
Trigger server update (runs update.py in background).
- JWT required
- Returns: `{ "status": "Update started" }`

### `POST /update_start_exit_program`
Exit for update process.
- JWT required
- Returns: `{ "status": "Update started" }`

## Cloud integration

### `POST /api/cloud/manage`
Manage cloud settings. The action parameter determines what happens:

**Enable/disable cloud:**
- Body: `{ "action": "enable", "enabled": true/false }`

**Delete auth data:**
- Body: `{ "action": "delete_auth" }`

**Sign up for cloud:**
- Body: `{ "action": "signup", "email": "...", "username": "...", "password": "..." }`
- Needs existing auth token in cloud settings

All require JWT auth.

## Role management

### `GET /api/role/get`
Get all roles from roles.json.
- JWT required
- Returns the complete roles object

### `POST /api/role/edit`
Update roles configuration.
- JWT required
- Body: JSON object with updated roles
- Returns: `{ "status": "Roles updated" }`

### `GET /api/role/self`
Get your role permissions for all endpoints.
- JWT required
- Returns object like `{ "/api/command": true, "/api/finder": false, ... }`

## Static files

These don't need auth:
- `GET /` - main index.html
- `GET /auth` - login page
- `GET /preview` - file preview page
- `GET /web/<filename>` - static files
- `GET /web/assets/<filename>` - asset files

## How JWT auth works

1. POST to `/api/user/login` with username/password
2. Get back a token that's valid for 24 hours
3. Send it in `Authorization: Bearer <token>` header for other requests

**Token errors:**
- Missing token: `401 Unauthorized`
- Expired: `401` with `"Token expired"`
- Invalid: `401` with `"Invalid token"`
- User doesn't exist: `401 Unauthorized`

I moved from API keys to JWT because it's more standard and handles expiration better.

## Access control

Users have role-based permissions defined in roles.json. There are also path-based read/write permissions per user.

Functions that check access:
- `has_access(path)` - can read from path
- `has_write_access(path)` - can write to path
- `is_accessible(address)` - can access endpoint based on role

## Database layout

**Users table:**
- id, username, password, name, ip, role, ftp_users, paths, settings, API_KEY, paths_write

**Logs table:**
- id, timestamp, action, ip

## Error responses

Pretty standard HTTP status codes:
- `400` - Bad request (missing params)
- `401` - Unauthorized (bad token/permissions)
- `404` - Not found
- `500` - Server error

That's basically it. The code in main.py has more details if you need them.