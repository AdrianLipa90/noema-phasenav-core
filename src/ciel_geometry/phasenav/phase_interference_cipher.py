"""Experimental PhaseNav phase-interference cipher.

The plaintext symbol is encoded as a semantic phase node. A keyed SHAKE256
phase field supplies carrier, background and permutation schedules. The valid
receiver reconstructs the same field and obtains a constructive matched-filter
beat. Without the key, the transmitted samples are intended to remain
noise-like.

This is a cryptographic research construction, not yet a standardized or
independently reviewed cipher.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import secrets
import struct
from dataclasses import dataclass

TAU = 2.0 * math.pi
_VERSION = "PNV-PHASE-CIPHER/1"
_SAMPLES_PER_SYMBOL = 32
_AMPLITUDE = 12_000.0
_SIGNAL_GAIN = 0.72
_NOISE_GAIN = 0.68


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _expand(key: bytes, nonce: bytes, domain: bytes, length: int) -> bytes:
    if not key:
        raise ValueError("key must not be empty")
    return hashlib.shake_256(
        b"PhaseNav\x00" + domain + b"\x00" + len(key).to_bytes(2, "big")
        + key + nonce
    ).digest(length)


def _u64_stream(key: bytes, nonce: bytes, domain: bytes, count: int) -> tuple[int, ...]:
    raw = _expand(key, nonce, domain, count * 8)
    return tuple(struct.unpack_from("!Q", raw, offset)[0] for offset in range(0, len(raw), 8))


def _phase_from_u64(value: int) -> float:
    return TAU * (value / 2**64)


def _symbol_phase(symbol: int) -> float:
    if not 0 <= symbol <= 255:
        raise ValueError("symbol outside byte range")
    return TAU * ((symbol + 0.5) / 256.0)


def _permutation(key: bytes, nonce: bytes, length: int) -> tuple[int, ...]:
    order = list(range(length))
    random_words = iter(_u64_stream(key, nonce, b"permutation", max(1, length)))
    for index in range(length - 1, 0, -1):
        swap = next(random_words) % (index + 1)
        order[index], order[swap] = order[swap], order[index]
    return tuple(order)


def _phase_field(key: bytes, nonce: bytes, symbol_count: int) -> tuple[tuple[float, float], ...]:
    count = symbol_count * _SAMPLES_PER_SYMBOL
    words = _u64_stream(key, nonce, b"phase-field", count * 2)
    return tuple(
        (_phase_from_u64(words[2 * i]), _phase_from_u64(words[2 * i + 1]))
        for i in range(count)
    )


def _quantize(value: float) -> int:
    return max(-32768, min(32767, int(round(value))))


def _render_symbol(symbol: int, field: tuple[tuple[float, float], ...], offset: int) -> tuple[int, ...]:
    semantic = _symbol_phase(symbol)
    samples = []
    for local in range(_SAMPLES_PER_SYMBOL):
        carrier, background = field[offset + local]
        value = _AMPLITUDE * (
            _SIGNAL_GAIN * math.cos(carrier + semantic)
            + _NOISE_GAIN * math.cos(background)
        )
        samples.append(_quantize(value))
    return tuple(samples)


def _decode_symbol(samples: tuple[int, ...], field: tuple[tuple[float, float], ...], offset: int) -> tuple[int, float, float]:
    best_symbol = 0
    best_score = -math.inf
    second_score = -math.inf
    for symbol in range(256):
        semantic = _symbol_phase(symbol)
        score = 0.0
        for local, observed in enumerate(samples):
            carrier, background = field[offset + local]
            cleaned = observed / _AMPLITUDE - _NOISE_GAIN * math.cos(background)
            score += cleaned * math.cos(carrier + semantic)
        if score > best_score:
            second_score = best_score
            best_score = score
            best_symbol = symbol
        elif score > second_score:
            second_score = score
    return best_symbol, best_score, best_score - second_score


def _derive_tag_key(key: bytes, nonce: bytes) -> bytes:
    return _expand(key, nonce, b"phase-auth", 32)


@dataclass(frozen=True)
class DecodeReceipt:
    plaintext: bytes
    minimum_margin: float
    mean_margin: float
    constructive_beat: float


def seal_phase_cipher(
    plaintext: bytes,
    key: bytes,
    *,
    context: str = "default",
    nonce: bytes | None = None,
) -> str:
    """Encode bytes as keyed semantic phase nodes immersed in keyed background."""
    nonce = secrets.token_bytes(16) if nonce is None else bytes(nonce)
    if len(nonce) < 16:
        raise ValueError("nonce must contain at least 16 bytes")
    context_bytes = context.encode("utf-8")
    context_key = _expand(key, nonce, b"context:" + context_bytes, 32)
    order = _permutation(context_key, nonce, len(plaintext))
    permuted = bytes(plaintext[index] for index in order)
    field = _phase_field(context_key, nonce, len(permuted))
    samples: list[int] = []
    for index, symbol in enumerate(permuted):
        samples.extend(_render_symbol(symbol, field, index * _SAMPLES_PER_SYMBOL))
    sample_bytes = struct.pack(f"!{len(samples)}h", *samples) if samples else b""
    header = {
        "version": _VERSION,
        "context": context,
        "nonce_b64": base64.urlsafe_b64encode(nonce).decode("ascii"),
        "symbol_count": len(plaintext),
        "samples_per_symbol": _SAMPLES_PER_SYMBOL,
        "samples_b64": base64.urlsafe_b64encode(sample_bytes).decode("ascii"),
    }
    tag = hmac.new(_derive_tag_key(context_key, nonce), _json_bytes(header), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(_json_bytes({**header, "tag": tag})).decode("ascii")


def open_phase_cipher(encoded: str, key: bytes) -> DecodeReceipt:
    envelope = json.loads(base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8"))
    if envelope.get("version") != _VERSION:
        raise ValueError("unsupported PhaseNav phase-cipher version")
    if int(envelope.get("samples_per_symbol", 0)) != _SAMPLES_PER_SYMBOL:
        raise ValueError("unsupported sample geometry")
    nonce = base64.urlsafe_b64decode(envelope["nonce_b64"].encode("ascii"))
    context = str(envelope["context"])
    count = int(envelope["symbol_count"])
    context_key = _expand(key, nonce, b"context:" + context.encode("utf-8"), 32)
    header = dict(envelope)
    supplied_tag = header.pop("tag")
    expected_tag = hmac.new(
        _derive_tag_key(context_key, nonce),
        _json_bytes(header),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(supplied_tag, expected_tag):
        raise ValueError("phase authentication failed")
    sample_bytes = base64.urlsafe_b64decode(envelope["samples_b64"].encode("ascii"))
    expected_samples = count * _SAMPLES_PER_SYMBOL
    if len(sample_bytes) != expected_samples * 2:
        raise ValueError("sample length mismatch")
    samples = struct.unpack(f"!{expected_samples}h", sample_bytes) if expected_samples else ()
    field = _phase_field(context_key, nonce, count)
    permuted = bytearray()
    margins = []
    beats = []
    for index in range(count):
        start = index * _SAMPLES_PER_SYMBOL
        block = tuple(samples[start:start + _SAMPLES_PER_SYMBOL])
        symbol, score, margin = _decode_symbol(block, field, start)
        permuted.append(symbol)
        margins.append(margin)
        beats.append(score / _SAMPLES_PER_SYMBOL)
    order = _permutation(context_key, nonce, count)
    plaintext = bytearray(count)
    for permuted_index, original_index in enumerate(order):
        plaintext[original_index] = permuted[permuted_index]
    return DecodeReceipt(
        plaintext=bytes(plaintext),
        minimum_margin=min(margins) if margins else math.inf,
        mean_margin=sum(margins) / len(margins) if margins else math.inf,
        constructive_beat=sum(beats) / len(beats) if beats else 0.0,
    )
