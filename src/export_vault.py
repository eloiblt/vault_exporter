import os
import json
import time
import hvac
from dotenv import load_dotenv
from vault_utils import login
load_dotenv()

BASE_FOLDER = os.getenv("BASE_FOLDER")
INTERMEDIARY_FOLDERS = os.getenv("INTERMEDIARY_FOLDERS")
FOLDERS = os.getenv("FOLDERS").split(",")

EXPORT_DIR = "./vault-export"

def remove_old_exports():
    for item in os.listdir("."):
        if item.startswith("vault-export") and os.path.isdir(item):
            import shutil
            shutil.rmtree(item)

def export_path(client, path=""):
    try:
        keys = client.secrets.kv.v2.list_secrets(
            path=path,
            mount_point=BASE_FOLDER
        )["data"]["keys"]

        for key in keys:
            full_path = f"{path}{key}"
            if key.endswith("/"):
                export_path(client, full_path)
            else:
                secret = client.secrets.kv.v2.read_secret_version(
                    path=full_path,
                    mount_point=BASE_FOLDER,
                    raise_on_deleted_version=True
                )["data"]["data"]

                local_dir = os.path.join(EXPORT_DIR, *path.strip("/").split("/")[1:])
                os.makedirs(local_dir, exist_ok=True)

                file_path = os.path.join(local_dir, f"{key}.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(secret, f, indent=2, ensure_ascii=False)

    except hvac.exceptions.InvalidPath:
        print(f"Aucun secret trouvé à : {path}")
        pass

if __name__ == "__main__":
    client = login()
    remove_old_exports()

    print("Export de Vault en cours...")
    for env in FOLDERS:
        export_path(client, f"{INTERMEDIARY_FOLDERS}/{env}/")

    with open(os.path.join(EXPORT_DIR, "export_time.txt"), "w") as f:
        f.write(str(time.time()))

    time.sleep(0.1)
    print("Export terminé")
