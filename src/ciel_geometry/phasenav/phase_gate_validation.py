"""Experimental PhaseNav gate lab for coding, authenticated envelopes and logic.

Security boundary
-----------------
This module is an experiment. PhaseNav contributes deterministic domain
separation and receipts. Confidentiality and integrity are provided by Python
stdlib primitives (PBKDF2-HMAC-SHA256, HMAC-SHA256 and a counter-mode HMAC
keystream). This construction has not been independently cryptanalyzed and is
not a replacement for a standard AEAD implementation.
"""
from __future__ import annotations

import ast
import base64
from dataclasses import dataclass
import hashlib
import hmac
import itertools
import json
import secrets
from typing import Mapping
import zlib

from .phase_gate_engine import PhaseGateEngine

_CODEC_VERSION = "PNV-CODEC/1"
_ENVELOPE_VERSION = "PNV-AUTH-ENVELOPE/1"
_LOGIC_VERSION = "PNV-LOGIC/1"
_PBKDF2_ROUNDS = 200_000


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _gate_receipt(data: bytes, *, domain: str) -> dict:
    """Build a PhaseNav receipt over arbitrary bytes without surrogate text.

    Raw binary is represented by canonical URL-safe base64 before entering the
    text-only phase gate. This mapping is deterministic, injective for byte
    strings and valid UTF-8 for every possible payload.
    """

    text = "bytes:b64:" + base64.urlsafe_b64encode(data).decode("ascii")
    result = PhaseGateEngine().step(f"{domain}\x1f{text}")
    stable = {
        "domain": domain,
        "phase_R": result["phase_R"],
        "ethical_score": result["ethical_score"],
        "soul_invariant": result["soul_invariant"],
        "collatz_seed": result["collatz_runtime"]["seed"],
        "collatz_orbit_length": result["collatz_runtime"]["orbit_length"],
        "parity_entropy": result["collatz_runtime"]["parity_entropy"],
        "euler_bridge": result["euler_bridge"],
        "information_flow": result["information_flow"],
    }
    stable["digest_sha256"] = hashlib.sha256(_canonical_json(stable)).hexdigest()
    return stable


def encode_phase_packet(payload: bytes, *, label: str = "data") -> str:
    """Reversible, non-secret transport encoding with integrity diagnostics."""
    receipt = _gate_receipt(payload, domain=f"codec:{label}")
    packet = {
        "version": _CODEC_VERSION,
        "label": label,
        "payload_b64": base64.urlsafe_b64encode(payload).decode("ascii"),
        "length": len(payload),
        "crc32": f"{zlib.crc32(payload) & 0xFFFFFFFF:08x}",
        "phase_receipt": receipt,
    }
    return base64.urlsafe_b64encode(_canonical_json(packet)).decode("ascii")


def decode_phase_packet(encoded: str) -> bytes:
    raw = base64.urlsafe_b64decode(encoded.encode("ascii"))
    packet = json.loads(raw.decode("utf-8"))
    if packet.get("version") != _CODEC_VERSION:
        raise ValueError("unsupported PhaseNav packet version")
    payload = base64.urlsafe_b64decode(packet["payload_b64"].encode("ascii"))
    if len(payload) != int(packet["length"]):
        raise ValueError("payload length mismatch")
    if f"{zlib.crc32(payload) & 0xFFFFFFFF:08x}" != packet["crc32"]:
        raise ValueError("CRC mismatch")
    expected = _gate_receipt(payload, domain=f"codec:{packet['label']}")
    if not hmac.compare_digest(
        expected["digest_sha256"],
        packet["phase_receipt"]["digest_sha256"],
    ):
        raise ValueError("PhaseNav receipt mismatch")
    return payload


def _derive_keys(secret: bytes, salt: bytes, receipt_digest: str) -> tuple[bytes, bytes]:
    material = hashlib.pbkdf2_hmac(
        "sha256",
        secret,
        salt + bytes.fromhex(receipt_digest),
        _PBKDF2_ROUNDS,
        dklen=64,
    )
    return material[:32], material[32:]


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < length:
        block = hmac.new(
            key,
            b"PNV-STREAM\x00" + nonce + counter.to_bytes(8, "big"),
            hashlib.sha256,
        ).digest()
        output.extend(block)
        counter += 1
    return bytes(output[:length])


def seal_phase_envelope(
    payload: bytes,
    secret: bytes,
    *,
    context: str,
    salt: bytes | None = None,
    nonce: bytes | None = None,
) -> str:
    """Create an experimental authenticated encrypted PhaseNav envelope."""
    if not secret:
        raise ValueError("secret must not be empty")
    salt = secrets.token_bytes(16) if salt is None else bytes(salt)
    nonce = secrets.token_bytes(16) if nonce is None else bytes(nonce)
    if len(salt) < 16 or len(nonce) < 16:
        raise ValueError("salt and nonce must contain at least 16 bytes")
    receipt = _gate_receipt(payload, domain=f"crypto:{context}")
    enc_key, mac_key = _derive_keys(secret, salt, receipt["digest_sha256"])
    stream = _keystream(enc_key, nonce, len(payload))
    ciphertext = bytes(a ^ b for a, b in zip(payload, stream))
    header = {
        "version": _ENVELOPE_VERSION,
        "context": context,
        "salt_b64": base64.urlsafe_b64encode(salt).decode("ascii"),
        "nonce_b64": base64.urlsafe_b64encode(nonce).decode("ascii"),
        "phase_receipt": receipt,
        "ciphertext_b64": base64.urlsafe_b64encode(ciphertext).decode("ascii"),
    }
    tag = hmac.new(mac_key, _canonical_json(header), hashlib.sha256).hexdigest()
    envelope = {**header, "tag_hmac_sha256": tag}
    return base64.urlsafe_b64encode(_canonical_json(envelope)).decode("ascii")


def open_phase_envelope(encoded: str, secret: bytes) -> bytes:
    envelope = json.loads(
        base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8")
    )
    if envelope.get("version") != _ENVELOPE_VERSION:
        raise ValueError("unsupported envelope version")
    salt = base64.urlsafe_b64decode(envelope["salt_b64"].encode("ascii"))
    nonce = base64.urlsafe_b64decode(envelope["nonce_b64"].encode("ascii"))
    ciphertext = base64.urlsafe_b64decode(
        envelope["ciphertext_b64"].encode("ascii")
    )
    receipt_digest = envelope["phase_receipt"]["digest_sha256"]
    enc_key, mac_key = _derive_keys(secret, salt, receipt_digest)
    header = dict(envelope)
    supplied_tag = header.pop("tag_hmac_sha256")
    expected_tag = hmac.new(
        mac_key,
        _canonical_json(header),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(supplied_tag, expected_tag):
        raise ValueError("authentication failed")
    stream = _keystream(enc_key, nonce, len(ciphertext))
    payload = bytes(a ^ b for a, b in zip(ciphertext, stream))
    expected_receipt = _gate_receipt(
        payload,
        domain=f"crypto:{envelope['context']}",
    )
    if not hmac.compare_digest(
        receipt_digest,
        expected_receipt["digest_sha256"],
    ):
        raise ValueError("PhaseNav plaintext receipt mismatch")
    return payload


_ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.UnaryOp,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.And,
    ast.Or,
    ast.Not,
)


def _parse_logic(expression: str) -> ast.Expression:
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"unsupported logical syntax: {type(node).__name__}")
        if isinstance(node, ast.Constant) and not isinstance(node.value, bool):
            raise ValueError("only Boolean constants are allowed")
    return tree


def _eval_logic(node: ast.AST, assignment: Mapping[str, bool]) -> bool:
    if isinstance(node, ast.Expression):
        return _eval_logic(node.body, assignment)
    if isinstance(node, ast.Name):
        if node.id not in assignment:
            raise ValueError(f"missing assignment for {node.id}")
        return bool(assignment[node.id])
    if isinstance(node, ast.Constant):
        return bool(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _eval_logic(node.operand, assignment)
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
        return all(_eval_logic(value, assignment) for value in node.values)
    if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
        return any(_eval_logic(value, assignment) for value in node.values)
    raise ValueError("invalid logical expression")


@dataclass(frozen=True)
class LogicReport:
    version: str
    expression: str
    variables: tuple[str, ...]
    classification: str
    rows: tuple[dict, ...]
    phase_receipt: dict

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "expression": self.expression,
            "variables": list(self.variables),
            "classification": self.classification,
            "rows": list(self.rows),
            "phase_receipt": self.phase_receipt,
        }


def validate_logic(expression: str) -> LogicReport:
    """Exhaustively classify a restricted Boolean expression."""
    tree = _parse_logic(expression)
    variables = tuple(sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}))
    rows = []
    outputs = []
    for values in itertools.product((False, True), repeat=len(variables)):
        assignment = dict(zip(variables, values))
        result = _eval_logic(tree, assignment)
        outputs.append(result)
        rows.append({"assignment": assignment, "result": result})
    if all(outputs):
        classification = "tautology"
    elif not any(outputs):
        classification = "contradiction"
    else:
        classification = "contingent"
    payload = _canonical_json(
        {
            "version": _LOGIC_VERSION,
            "expression": expression,
            "variables": variables,
            "rows": rows,
            "classification": classification,
        }
    )
    return LogicReport(
        version=_LOGIC_VERSION,
        expression=expression,
        variables=variables,
        classification=classification,
        rows=tuple(rows),
        phase_receipt=_gate_receipt(payload, domain="logic"),
    )
