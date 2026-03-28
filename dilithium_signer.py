import json
import hashlib
from dilithium_py.dilithium import Dilithium2


# ==============================
# KEY GENERATION
# ==============================
def generate_keys():
    pk, sk = Dilithium2.keygen()
    print("✅ Key pair generated")
    print(f"   Public key size : {len(pk)} bytes")
    print(f"   Private key size: {len(sk)} bytes")
    return pk, sk


# ==============================
# SIGN PAYLOAD
# ==============================
def sign_payload(payload: dict, sk: bytes) -> bytes:
    # Serialize payload to bytes (sorted keys for consistency)
    payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

    # Hash it first for cleaner signing
    payload_hash = hashlib.sha256(payload_bytes).digest()

    # Sign with Dilithium
    signature = Dilithium2.sign(sk, payload_hash)

    return signature, payload_hash


# ==============================
# VERIFY SIGNATURE
# ==============================
def verify_signature(payload_hash: bytes, signature: bytes, pk: bytes) -> bool:
    try:
        result = Dilithium2.verify(pk, payload_hash, signature)
        return result
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False


# ==============================
# MAIN DEMO
# ==============================
if __name__ == "__main__":

    print("\n" + "=" * 55)
    print("  Dilithium Post-Quantum Signature — Supply Chain Demo")
    print("=" * 55 + "\n")

    # Step 1: Generate keys
    print("🔑 Step 1: Generating Dilithium2 Key Pair...")
    pk, sk = generate_keys()

    # Step 2: Create a shipment payload
    print("\n📦 Step 2: Creating Shipment Payload...")
    payload = {
        "shipmentId"  : "SHP001",
        "from"        : "Manufacturer_A",
        "to"          : "Warehouse_B",
        "goods"       : "Electronics",
        "quantity"    : 500,
        "timestamp"   : "2025-03-22"
    }
    print(f"   Payload: {json.dumps(payload, indent=6)}")

    # Step 3: Sign
    print("\n✍️  Step 3: Signing payload with Dilithium private key...")
    signature, payload_hash = sign_payload(payload, sk)
    print(f"   Payload hash : {payload_hash.hex()}")
    print(f"   Signature    : {signature.hex()[:64]}... (truncated)")
    print(f"   Signature size: {len(signature)} bytes")

    # Step 4: Verify valid signature
    print("\n🔍 Step 4: Verifying signature with public key...")
    is_valid = verify_signature(payload_hash, signature, pk)
    print(f"   Result: {'✅ Signature VALID' if is_valid else '❌ Signature INVALID'}")

    # Step 5: Tamper test
    print("\n⚠️  Step 5: Tamper test — modifying payload after signing...")
    tampered_payload = payload.copy()
    tampered_payload["quantity"] = 9999  # attacker changes quantity

    _, tampered_hash = sign_payload(tampered_payload, sk)
    is_valid_tampered = verify_signature(tampered_hash, signature, pk)
    print(f"   Tampered payload hash : {tampered_hash.hex()}")
    print(f"   Result: {'✅ Valid' if is_valid_tampered else '❌ INVALID — Tampering detected!'}")

    print("\n" + "=" * 55)
    print("  Summary")
    print("=" * 55)
    print(f"  Original signature valid : ✅ {is_valid}")
    print(f"  Tampered signature valid : ❌ {is_valid_tampered}")
    print(f"  Quantum-safe algorithm   : Dilithium2 (ML-DSA)")
    print("=" * 55 + "\n")