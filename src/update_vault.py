import os
import json
import time
from dotenv import load_dotenv
from vault_utils import login
load_dotenv()

BASE_FOLDER = os.getenv("BASE_FOLDER")
INTERMEDIARY_FOLDERS = os.getenv("INTERMEDIARY_FOLDERS")
FOLDERS = os.getenv("FOLDERS").split(",")

EXPORT_DIR = "./vault-export"

def update_vault(client):
    with open(os.path.join(EXPORT_DIR, "export_time.txt"), "r") as f:
        since = float(f.read().strip())

    print(f"Recherche de secrets modifiés...")
    modified_files = []
    for dirpath, _, filenames in os.walk(EXPORT_DIR):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            mtime = os.path.getmtime(filepath)
            if mtime > since and not filepath.endswith("export_time.txt"):
                modified_files.append(filepath)

    print(f"{len(modified_files)} fichier(s) modifié(s)\n")

    for filepath in modified_files:
        relative_path = os.path.relpath(filepath, EXPORT_DIR)
        vault_path = os.path.splitext(relative_path)[0].replace("\\", "/")
        vault_path = f"{INTERMEDIARY_FOLDERS}/{vault_path}"

        filepath_display = filepath.replace("\\", "/")
        answer = input(f'Appliquer "{filepath_display}" sur "{BASE_FOLDER}/{vault_path}" ? (Y/n) ').strip().lower()

        if answer in ("", "y", "yes"):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            client.secrets.kv.v2.create_or_update_secret(
                path=vault_path,
                secret=data,
                mount_point=BASE_FOLDER
            )

            print(f'"{filepath_display}" appliqué avec succès sur "{BASE_FOLDER}/{vault_path}"')
        else:
            print("Ignoré.")
        print("")

    with open(os.path.join(EXPORT_DIR, "export_time.txt"), "w") as f:
        f.write(str(time.time()))

if __name__ == "__main__":
    client = login()
    update_vault(client)