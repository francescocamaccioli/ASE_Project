import requests
import json

"""
ATTENZIONE: questo script viene eseguito ad ogni avvio del container
TODO: Aggiungere un controllo per evitare di eseguirlo se è già stato eseguito in precedenza?
"""



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
        


if __name__ == "__main__":
    url = "https://127.0.0.1:5000/gatchas"
    
    objects = [
        {"name": "ARTPOP - 2019 Reissue", "rarity": "comune", "file_path": './testimg/common/artpop-vinyl-reissue-4_orig.png'},
        {"name": "MATTEO CAMBIA NOME", "rarity": "comune", "file_path": './testimg/common/chromatica-picture-disc-3_orig.png'}, #TODO: matteo cambia nome
        # TODO: Add more objects here
    ]
    
    for obj in objects:
        send_request(url, obj["name"], obj["rarity"], obj["file_path"])
        