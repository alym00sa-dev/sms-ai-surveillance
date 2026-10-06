"""Regenerate system_prompt.txt and output_contract.txt from the prompt README."""
from . import CONTRACT_FILE, README, SYSTEM_FILE, extract_from_readme

if __name__ == "__main__":
    system, contract, version = extract_from_readme(README.read_text(encoding="utf-8"))
    SYSTEM_FILE.write_text(system + "\n", encoding="utf-8")
    CONTRACT_FILE.write_text(contract + "\n", encoding="utf-8")
    print(f"synced prompt {version}")
