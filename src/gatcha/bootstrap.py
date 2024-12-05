import requests
import json
import os

STATE_FILE = './already_bootstrapped.txt'

def send_request(url, name, rarity, file_path):
    payload = {'json': json.dumps({
        "name": name,
        "rarity": rarity
    })}

    files = [
        ('file', (file_path.split('/')[-1], open(file_path, 'rb'), 'application/octet-stream'))
    ]

    response = requests.request("POST", url, data=payload, files=files, verify=False)

    if response.status_code == 200:
        print(f"Successfully inserted images from {file_path}.")
    else:
        print(f"Failed to insert images from {file_path}. Status code: {response.status_code}, Response: {response.text}")

def main():
    if os.path.exists(STATE_FILE):
        print("Bootstrap has already been executed. Exiting.")
        return

    url = "https://127.0.0.1:5000/gatchas"
    
    objects = [
        {"name": "ARTPOP - 2019 Reissue", "rarity": "comune", "file_path": './testimg/common/artpop-vinyl-reissue-4_orig.png'},
        {"name": "MATTEO CAMBIA NOME", "rarity": "comune", "file_path": './testimg/common/chromatica-picture-disc-3_orig.png'}, #TODO: matteo cambia nome
        # TODO: Add more objects here
    ]
    
    for obj in objects:
        send_request(url, obj["name"], obj["rarity"], obj["file_path"])

    # Create the state file to indicate that the script has been executed
    with open(STATE_FILE, 'w') as f:
        f.write('Script executed')

if __name__ == "__main__":
    main()