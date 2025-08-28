# Vault exporter / importer 

Scripts for exporting/importing secrets from Hashicorp Vault, while preserving the folder structure

> This script assumes that the vault command is installed and available in the path.

```python
# Generates the same tree structure as the target Vault in the current folder.
python ./src/export_vault.py

# Apply all modified files to Vault.
python ./src/update_vault.py
```

