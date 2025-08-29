import os
import json
import time
import hvac
from dotenv import load_dotenv
load_dotenv()

VAULT_ADDR = os.getenv("VAULT_ADDR")
VAULT_NAMESPACE = os.getenv("VAULT_NAMESPACE")

BASE_FOLDER = os.getenv("BASE_FOLDER")
INTERMEDIARY_FOLDERS = os.getenv("INTERMEDIARY_FOLDERS")
FOLDERS = os.getenv("FOLDERS").split(",")

EXPORT_DIR = "./vault-export"

def ensure_login():
    client_args = dict(url=VAULT_ADDR, namespace=VAULT_NAMESPACE)
    client = hvac.Client(**client_args)

    if client.is_authenticated():
        print("\nAlready logged to Vault\n")
        return client

    raise Exception()

def update_vault(client):
    with open(os.path.join(EXPORT_DIR, "infos.txt"), "r") as f:
        infos = f.read().split("\n")

    print(f"Recherche de secrets modifiés...\n")

    all_files_path = []
    added_files = []
    deleted_files = []
    modified_files = []
    for info in infos:
        if not info.strip():
            continue
        file_path, date = info.split(" --- ")
        date = float(date.strip())

        all_files_path.append(file_path)

        if not os.path.exists(file_path):
            deleted_files.append(file_path)
            continue

        mtime = os.path.getmtime(file_path)
        if mtime > date:
            modified_files.append(file_path)

    for dirpath, _, filenames in os.walk(EXPORT_DIR):
        for filename in filenames:
            if filename == "infos.txt":
                continue
            file_path = os.path.join(dirpath, filename)

            if file_path not in all_files_path:
                added_files.append(file_path)

    print(f"{len(modified_files)} fichier(s) modifié(s)")
    print(f"{len(added_files)} fichier(s) ajoutés(s)")
    print(f"{len(deleted_files)} fichier(s) supprimés(s)\n")

    if not (modified_files or added_files or deleted_files):
        print("Aucun changement détecté. Exiting.")
        return

    for file_path in modified_files + added_files:
        relative_path = os.path.relpath(file_path, EXPORT_DIR)
        vault_path = os.path.splitext(relative_path)[0].replace("\\", "/")
        vault_path = f"{INTERMEDIARY_FOLDERS}/{vault_path}"

        file_path_display = file_path.replace("\\", "/")

        text = "Appliquer la modification de"
        if file_path in added_files:
            text = "Ajouter"
        answer = input(f'{text} "{file_path_display}" sur "{BASE_FOLDER}/{vault_path}" ? (Y/n) ').strip().lower()

        if answer in ("", "y", "yes"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            client.secrets.kv.v2.create_or_update_secret(
                path=vault_path,
                secret=data,
                mount_point=BASE_FOLDER
            )

            text = "modifié"
            if file_path in added_files:
                text = "ajouté"
            print(f'Secret {text} : "{BASE_FOLDER}/{vault_path}"')
        else:
            print("Ignoré.")
        print("")

    for file_path in deleted_files:
        relative_path = os.path.relpath(file_path, EXPORT_DIR)
        vault_path = os.path.splitext(relative_path)[0].replace("\\", "/")
        vault_path = f"{INTERMEDIARY_FOLDERS}/{vault_path}"

        answer = input(f'Supprimer "{BASE_FOLDER}/{vault_path}" ? (Y/n) ').strip().lower()

        if answer in ("", "y", "yes"):
            client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=vault_path,
                mount_point=BASE_FOLDER
            )
            print(f'Secret supprimé : "{BASE_FOLDER}/{vault_path}"')
        else:
            print("Ignoré.")
        print("")

    os.remove(os.path.join(EXPORT_DIR, "infos.txt"))
    for dirpath, _, filenames in os.walk(EXPORT_DIR):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)

            with open(os.path.join(EXPORT_DIR, "infos.txt"), "a") as f:
                mtime = os.path.getmtime(file_path)
                f.write(f"{file_path} --- {str(mtime)}\n")

if __name__ == "__main__":
    start_time = time.time()

    try:
        client = ensure_login()
    except Exception as e:
        print("Client is not authenticated. Please login using 'login_vault.py' first.")
        exit(1)

    update_vault(client)

    print(f"Durée totale du script : {time.time() - start_time:.2f}s\n")