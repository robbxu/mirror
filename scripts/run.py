import requests

BASE_URL = "http://localhost:8010/api/v1/"

def main():
    interaction_id = None
    while True:
        command = input("\nEnter a command.\n")
        if command.startswith("set context: "):
            id = command[13:]
            if id == "new":
                response = requests.post(BASE_URL + "interact/create")
                print("Response: ")
                print(response.json())
                interaction_id = response.json()["interaction_id"]
                continue
            elif len(id) > 10:
                response = requests.get(BASE_URL + "interact/interaction/" + id)
                print("Response: ")
                print(response.json())
                interaction_id = id
                continue
            else:
                print("Unrecognized input. Please try again.")
        if command.startswith("upload: "):
            file_path = command[8:]
            response = upload_file(file_path)
            print("Response: ")
            print(response)
            continue
        elif command.startswith("message: "):
            message = command[9:]
            response = send_message(message, interaction_id)
            print("Response: ")
            print(response)
            continue
        elif command.startswith("status: "):
            task_id = command[8:]
            response = requests.get(BASE_URL + f"analysis/task/{task_id}")
            print("Response: ")
            print(response.json())
            continue
        elif command == "exit":
            break
        else:
            print("Command not recognized. The commands available are:")
            print("set context: <interaction_id> | 'new'")
            print("upload: <file_path>")
            print("message: <message>")
            print("status: <celery_task_id>")
            print("exit")
    

def upload_file(file_path: str = 'data/journal_full.docx', endpoint: str = "interact/upload"):
    with open(file_path, 'rb') as file:
        files = {'file': (file_path, file)}
        response = requests.post(BASE_URL + endpoint, files=files)
        return response.json()

def send_message(message: str, interaction_id: str, endpoint: str = "interact/message"):
    data = {"id": interaction_id, "message": message}
    response = requests.post(BASE_URL + endpoint, json=data)
    return response.json()


def initialize():
    endpoint = 'analysis/initialize'
    response = requests.post(BASE_URL + endpoint)
    print(response.json())
  

if __name__ == "__main__":
    initialize()
    main()