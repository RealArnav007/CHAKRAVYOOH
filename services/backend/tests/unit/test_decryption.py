import pytest
import nacl.public
import nacl.encoding
from src.security.encryption.x25519_box import decrypt_payload
from src.config import get_settings

def test_x25519_decryption_success(crypto_keys, monkeypatch):
    """Test successful SealedBox decryption using the backend's private key."""
    # Temporarily override the settings backend key for this test
    settings = get_settings()
    monkeypatch.setattr(settings, "BACKEND_X25519_PRIVATE_KEY", crypto_keys["backend_priv"])
    
    plaintext = b"critical medical emergency payload"
    
    # Simulate the Android client encrypting the payload with our public key
    backend_pub = nacl.public.PublicKey(crypto_keys["backend_pub"], encoder=nacl.encoding.HexEncoder)
    sealed_box = nacl.public.SealedBox(backend_pub)
    encrypted_payload = sealed_box.encrypt(plaintext)
    
    payload_enc_hex = nacl.encoding.HexEncoder.encode(encrypted_payload).decode("utf-8")
    
    # Decrypt
    decrypted = decrypt_payload(payload_enc_hex)
    assert decrypted == plaintext.decode("utf-8")

def test_x25519_decryption_failure():
    """Test decryption failure on corrupt or invalid hex payload."""
    with pytest.raises(ValueError, match="Failed to decrypt payload"):
        decrypt_payload("invalidhexdata00000")
