import os
import hvac
import subprocess
from dotenv import load_dotenv
load_dotenv()

VAULT_ADDR = os.getenv("VAULT_ADDR")
VAULT_NAMESPACE = os.getenv("VAULT_NAMESPACE")

def login():
    client_args = dict(url=VAULT_ADDR, namespace=VAULT_NAMESPACE)
    client = hvac.Client(**client_args)

    if client.is_authenticated():
        print("\nSuccessfully logged in via Vault CLI\n")
        return client

    login_cmd = [
        "vault.exe", "login",
        f"-namespace={VAULT_NAMESPACE}",
        f"-address={VAULT_ADDR}",
        "-method=oidc"
    ]
    result = subprocess.run(login_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Vault CLI login failed: {result.stderr}")

    print("\nSuccessfully logged in via Vault CLI\n")
    return client
