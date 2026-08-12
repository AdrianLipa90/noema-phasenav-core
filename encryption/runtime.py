"""Executable façade for the experimental PhaseNav phase-interference cipher.

This remains a research cipher and is not promoted as standardized cryptography.
"""
from __future__ import annotations

from ciel_geometry.phasenav.phase_interference_cipher import (
    DecodeReceipt,
    open_phase_cipher,
    seal_phase_cipher,
)


def seal_text(text: str, key: bytes, *, context: str = "default", nonce: bytes | None = None) -> str:
    return seal_phase_cipher(text.encode("utf-8"), key, context=context, nonce=nonce)


def open_text(encoded: str, key: bytes) -> tuple[str, DecodeReceipt]:
    receipt = open_phase_cipher(encoded, key)
    return receipt.plaintext.decode("utf-8"), receipt


__all__ = ["DecodeReceipt", "open_phase_cipher", "open_text", "seal_phase_cipher", "seal_text"]
