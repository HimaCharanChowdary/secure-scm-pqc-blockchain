import os
from dilithium_py.dilithium import Dilithium2

# CONFIGURATION
KEYS_DIR        = "keys"
PUBLIC_KEY_FILE = os.path.join(KEYS_DIR, "auditor_public.key")
PRIVATE_KEY_FILE = os.path.join(KEYS_DIR, "auditor_private.key")


def generate_and_save_keys():

    # Safety check — don't overwrite existing keys
    if os.path.exists(PUBLIC_KEY_FILE) or os.path.exists(PRIVATE_KEY_FILE):
        print("⚠️  Keys already exist at:")
        print(f"   {PUBLIC_KEY_FILE}")
        print(f"   {PRIVATE_KEY_FILE}")
        print("\n   Delete them manually if you want to regenerate.")
        return

    # Create keys directory
    os.makedirs(KEYS_DIR, exist_ok=True)

    print("\n🔑 Generating Dilithium2 key pair...")
    pk, sk = Dilithium2.keygen()

    # Save public key
    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(pk)

    # Save private key
    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(sk)

    print(f"✅ Keys saved successfully!\n")
    print(f"   Public key  → {PUBLIC_KEY_FILE}  ({len(pk)} bytes)")
    print(f"   Private key → {PRIVATE_KEY_FILE} ({len(sk)} bytes)")
    print(f"\n⚠️  Keep auditor_private.key safe — never share it!")


def load_keys():
    if not os.path.exists(PUBLIC_KEY_FILE):
        raise FileNotFoundError(f"Public key not found at {PUBLIC_KEY_FILE}. Run generate_keys.py first.")

    if not os.path.exists(PRIVATE_KEY_FILE):
        raise FileNotFoundError(f"Private key not found at {PRIVATE_KEY_FILE}. Run generate_keys.py first.")

    with open(PUBLIC_KEY_FILE, "rb") as f:
        pk = f.read()

    with open(PRIVATE_KEY_FILE, "rb") as f:
        sk = f.read()

    return pk, sk


if __name__ == "__main__":
    print("=" * 50)
    print("  Dilithium2 Key Generator")
    print("=" * 50)
    generate_and_save_keys()