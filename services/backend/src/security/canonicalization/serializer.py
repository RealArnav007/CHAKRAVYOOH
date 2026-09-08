from src.sos.validation.validator import SosPacket


def serialize_canonical_bytes(packet: SosPacket) -> bytes:
    """
    Serializes the immutable region of the SosPacket into a strict, byte-exact
    canonical string for Ed25519 signature verification.
    
    WARNING [A] Android Client Developer:
    Floating point parsing and serialization must perfectly match Python's formatting.
    Android MUST use: `String.format(Locale.US, "%.6f", value)` for coordinates,
    and `String.format(Locale.US, "%.4f", confidence)`.
    Failure to do this will result in a 401 BAD_SIGNATURE.
    """
    parts = [
        str(packet.msg_id),
        str(packet.origin_id),
        str(packet.origin_key_id),
        str(packet.created_at),
        str(packet.nonce),
        f"{float(packet.lat):.6f}",
        f"{float(packet.lon):.6f}",
        f"{float(packet.acc):.2f}",
        str(packet.trigger_type),
        str(packet.request_type),
        str(packet.severity),
        str(packet.regex_score),
        str(packet.local_model_score),
        f"{float(packet.confidence):.4f}",
        str(packet.payload_enc)
    ]
    return "|".join(parts).encode("utf-8")
