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

    url = "https://127.0.0.1:5000/gatchas/initialization"
    
    objects = [
        {"name": "ARTPOP - 2019 Reissue", "rarity": "comune", "file_path": './testimg/common/artpop-vinyl-reissue-4_orig.png'},
        {"name": "Chromatica - Picture Disc", "rarity": "comune", "file_path": './testimg/common/chromatica-picture-disc-3_orig.png'},
        {"name": "The Fame - 2008 Original Pressing", "rarity": "comune", "file_path": './testimg/common/the-fame-vinyl-3_orig.png'},
        {"name": "Chromatica - Silver Vinyl", "rarity": "comune", "file_path": './testimg/common/chromatica-silver-vinyl-urban-outfitters-44_orig.png'},
        {"name": "Joanne - 2016 Original Pressing", "rarity": "comune", "file_path": './testimg/common/joanne-vinyl-6_2_orig-2.png'},
        {"name": "Bad Romance - 7\" Single", "rarity": "raro", "file_path": './testimg/rare/R-2013514-1351012345-8398.jpg'},
        {"name": "Telephone - 7\" Single", "rarity": "raro", "file_path": './testimg/rare/R-2190827-1597019191-2463.jpg'},
        {"name": "Alejandro - 7\" Single", "rarity": "raro", "file_path": './testimg/rare/R-2338307-1323726152.jpg'},
        {"name": "The Fame - 2024 Picture Disc", "rarity": "raro", "file_path": './testimg/rare/R-30324680-1712446908-1471.jpg'},
        {"name": "Joanne - Fluorescent Pink Vinyl", "rarity": "epico", "file_path": './testimg/epic/joanne-vinyl-urban-outfitters-6_orig.jpg'},
        {"name": "Chromatica - 2021 RSD Exclusive Yellow Vinyl", "rarity": "epico", "file_path": './testimg/epic/chromatica-deluxe-trifold-vinyl-rsd-exclusive-9_orig.jpg'},
        {"name": "Born This Way - Red Vinyl", "rarity": "epico", "file_path": './testimg/epic/born-this-way-red-vinyl-urban-outfitters-5_orig.jpg'},
        {"name": "Born This Way - Box Set, Numbered, 9x12\" Picture Discs", "rarity": "leggendario", "file_path": './testimg/legendary/R-3171033-1330104327.jpg'},
        {"name": "The Fame + The Fame Monster Box Set: The Fame Monster Silver Vinyl", "rarity": "leggendario", "file_path": './testimg/legendary/the-fame-monster-deluxe-edition-vinyl-6_orig.png'}
    ]
    
    for obj in objects:
        send_request(url, obj["name"], obj["rarity"], obj["file_path"])

    # Create the state file to indicate that the script has been executed
    with open(STATE_FILE, 'w') as f:
        f.write('Script executed')

if __name__ == "__main__":
    main()