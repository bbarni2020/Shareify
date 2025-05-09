import requests

BASE_URL = "http://localhost:6969/api"
API_KEY = "ABC" 
HEADERS = {"X-API-KEY": API_KEY}

def list_items(path=None):
    params = {"path": path} if path else {}
    response = requests.get(f"{BASE_URL}/finder", headers=HEADERS, params=params)
    print(response.json())

def execute_command(command):
    payload = {"command": command}
    response = requests.get(f"{BASE_URL}/command", headers=HEADERS, json=payload)
    print(response.json())

def create_folder(folder_name, path=None):
    payload = {"folder_name": folder_name, "path": path}
    response = requests.post(f"{BASE_URL}/create_folder", headers=HEADERS, json=payload)
    print(response.json())

def delete_folder(path):
    payload = {"path": path}
    response = requests.post(f"{BASE_URL}/delete_folder", headers=HEADERS, json=payload)
    print(response.json())

def rename_folder(old_name, new_name, path=None):
    payload = {"folder_name": old_name, "new_name": new_name, "path": path}
    response = requests.post(f"{BASE_URL}/rename_folder", headers=HEADERS, json=payload)
    print(response.json())
def resources():
    response = requests.get(f"{BASE_URL}/resources", headers=HEADERS)
    print(response.json())
def login(username, password):
    payload = {"username": username, "password": password}
    response = requests.post(f"{BASE_URL}/user/login", json=payload)
    print(response.json())

if __name__ == "__main__":

    #print("\nListing items in base path:")
    #list_items()

    #print("\nListing items in a subdirectory:")
    #list_items("hello")

    #print("\nExecuting a command:")
    #execute_command("ls")

    #print("\nCreating a folder:")
    #create_folder("new_folder")
    #create_folder("new_folder2")

    #print("\nDeleting a folder:")
    #delete_folder("new_folder")

    #print("\nRenaming a folder:")
    #rename_folder("new_folder2", "new_folder_name")
    resources()
    login("admin", "root")