import base64
import json

import pytest

from ciel_geometry.phasenav.phase_gate_validation import (
    decode_phase_packet,
    encode_phase_packet,
    open_phase_envelope,
    seal_phase_envelope,
    validate_logic,
)


def test_phase_codec_round_trip_binary_payload():
    payload = bytes(range(256)) + "PhaseNav — kodowanie".encode("utf-8")
    encoded = encode_phase_packet(payload, label="binary-fixture")
    assert decode_phase_packet(encoded) == payload


def test_phase_codec_detects_payload_tampering():
    encoded = encode_phase_packet(b"canonical payload", label="tamper")
    packet = json.loads(base64.urlsafe_b64decode(encoded).decode("utf-8"))
    payload = bytearray(base64.urlsafe_b64decode(packet["payload_b64"]))
    payload[0] ^= 1
    packet["payload_b64"] = base64.urlsafe_b64encode(bytes(payload)).decode("ascii")
    tampered = base64.urlsafe_b64encode(
        json.dumps(packet, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    with pytest.raises(ValueError):
        decode_phase_packet(tampered)


def test_authenticated_phase_envelope_round_trip_is_deterministic_with_fixed_inputs():
    payload = b"phase-gated confidential fixture"
    secret = b"correct horse battery staple"
    salt = bytes(range(16))
    nonce = bytes(range(16, 32))
    first = seal_phase_envelope(
        payload,
        secret,
        context="unit-test",
        salt=salt,
        nonce=nonce,
    )
    second = seal_phase_envelope(
        payload,
        secret,
        context="unit-test",
        salt=salt,
        nonce=nonce,
    )
    assert first == second
    assert open_phase_envelope(first, secret) == payload


def test_authenticated_phase_envelope_changes_with_nonce_and_context():
    payload = b"same plaintext"
    secret = b"shared secret"
    salt = b"S" * 16
    a = seal_phase_envelope(payload, secret, context="A", salt=salt, nonce=b"A" * 16)
    b = seal_phase_envelope(payload, secret, context="A", salt=salt, nonce=b"B" * 16)
    c = seal_phase_envelope(payload, secret, context="B", salt=salt, nonce=b"A" * 16)
    assert len({a, b, c}) == 3


def test_authenticated_phase_envelope_rejects_wrong_secret():
    encoded = seal_phase_envelope(
        b"payload",
        b"right secret",
        context="auth",
        salt=b"1" * 16,
        nonce=b"2" * 16,
    )
    with pytest.raises(ValueError, match="authentication failed"):
        open_phase_envelope(encoded, b"wrong secret")


def test_authenticated_phase_envelope_rejects_ciphertext_tampering():
    encoded = seal_phase_envelope(
        b"payload",
        b"secret",
        context="auth",
        salt=b"1" * 16,
        nonce=b"2" * 16,
    )
    envelope = json.loads(base64.urlsafe_b64decode(encoded).decode("utf-8"))
    ciphertext = bytearray(base64.urlsafe_b64decode(envelope["ciphertext_b64"]))
    ciphertext[0] ^= 1
    envelope["ciphertext_b64"] = base64.urlsafe_b64encode(bytes(ciphertext)).decode("ascii")
    tampered = base64.urlsafe_b64encode(
        json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    with pytest.raises(ValueError, match="authentication failed"):
        open_phase_envelope(tampered, b"secret")


def test_logic_validator_classifies_tautology_contradiction_and_contingency():
    assert validate_logic("a or not a").classification == "tautology"
    assert validate_logic("a and not a").classification == "contradiction"
    report = validate_logic("a and (b or not c)")
    assert report.classification == "contingent"
    assert len(report.rows) == 8
    assert report.phase_receipt["digest_sha256"]


def test_logic_receipt_is_deterministic():
    first = validate_logic("(a and b) or (not a and c)")
    second = validate_logic("(a and b) or (not a and c)")
    assert first.to_dict() == second.to_dict()


def test_logic_validator_rejects_code_execution_syntax():
    with pytest.raises(ValueError):
        validate_logic("__import__('os').system('echo unsafe')")
