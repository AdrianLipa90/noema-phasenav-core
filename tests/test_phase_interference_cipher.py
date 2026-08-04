import base64
import json
import math

import pytest

from ciel_geometry.phasenav.phase_interference_cipher import (
    open_phase_cipher,
    seal_phase_cipher,
)


def test_phase_interference_round_trip_all_byte_values():
    plaintext = bytes(range(256))
    encoded = seal_phase_cipher(
        plaintext,
        b"phase-key",
        context="all-bytes",
        nonce=bytes(range(16)),
    )
    receipt = open_phase_cipher(encoded, b"phase-key")
    assert receipt.plaintext == plaintext
    assert receipt.minimum_margin > 0.0
    assert receipt.constructive_beat > 0.0


def test_phase_interference_nonce_and_context_separate_waveforms():
    plaintext = b"same semantic payload"
    key = b"phase-key"
    a = seal_phase_cipher(plaintext, key, context="A", nonce=b"A" * 16)
    b = seal_phase_cipher(plaintext, key, context="A", nonce=b"B" * 16)
    c = seal_phase_cipher(plaintext, key, context="B", nonce=b"A" * 16)
    assert len({a, b, c}) == 3


def test_phase_interference_wrong_key_has_no_valid_constructive_decode():
    encoded = seal_phase_cipher(
        b"hidden in keyed background",
        b"correct-key",
        context="covert",
        nonce=b"N" * 16,
    )
    with pytest.raises(ValueError, match="phase authentication failed"):
        open_phase_cipher(encoded, b"wrong-key")


def test_phase_interference_detects_sample_tampering():
    encoded = seal_phase_cipher(
        b"tamper target",
        b"secret",
        context="integrity",
        nonce=b"I" * 16,
    )
    envelope = json.loads(base64.urlsafe_b64decode(encoded).decode("utf-8"))
    samples = bytearray(base64.urlsafe_b64decode(envelope["samples_b64"]))
    samples[len(samples) // 2] ^= 0x40
    envelope["samples_b64"] = base64.urlsafe_b64encode(bytes(samples)).decode("ascii")
    tampered = base64.urlsafe_b64encode(
        json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    with pytest.raises(ValueError, match="phase authentication failed"):
        open_phase_cipher(tampered, b"secret")


def test_phase_interference_waveform_is_centered_and_nonconstant():
    encoded = seal_phase_cipher(
        b"A" * 128,
        b"statistical-key",
        context="noise-shape",
        nonce=b"S" * 16,
    )
    envelope = json.loads(base64.urlsafe_b64decode(encoded).decode("utf-8"))
    raw = base64.urlsafe_b64decode(envelope["samples_b64"])
    values = [int.from_bytes(raw[i:i + 2], "big", signed=True) for i in range(0, len(raw), 2)]
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    assert abs(mean) < 800.0
    assert variance > 1_000_000.0
    assert len(set(values)) > 100


def test_phase_interference_empty_payload_round_trip():
    encoded = seal_phase_cipher(
        b"",
        b"key",
        context="empty",
        nonce=b"E" * 16,
    )
    receipt = open_phase_cipher(encoded, b"key")
    assert receipt.plaintext == b""
    assert math.isinf(receipt.minimum_margin)
