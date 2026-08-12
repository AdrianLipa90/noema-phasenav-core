"""Deterministic smoke validation for the PhaseNav research cipher."""
from __future__ import annotations

from .runtime import open_text, seal_text


def self_test() -> dict:
    key = b"PhaseNav-integrity-self-test-key"
    nonce = bytes(range(16))
    message = "PhaseNav 36D integrity"
    encoded = seal_text(message, key, context="repo-integrity", nonce=nonce)
    decoded, receipt = open_text(encoded, key)
    if decoded != message:
        raise RuntimeError("phase cipher round trip mismatch")
    return {
        "status": "PASS",
        "plaintext_bytes": len(message.encode("utf-8")),
        "minimum_margin": float(receipt.minimum_margin),
        "mean_margin": float(receipt.mean_margin),
        "constructive_beat": float(receipt.constructive_beat),
    }


__all__ = ["self_test"]
