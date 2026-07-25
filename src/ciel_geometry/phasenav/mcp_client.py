"""MCP Client — JSON-RPC stdio to noema_surface MCP server.
Zero deps. Pure stdlib. PhaseNav integrated."""

import json as _json
import os as _os
import subprocess as _subprocess
import sys as _sys

_MCP_SERVER_PATH = "/home/adrian/.codex/noema_surface/noema_surface_mcp_server.py"
_MCP_PROCESS = None
_MCP_REQUEST_ID = 0

def _ensure_mcp():
    global _MCP_PROCESS, _MCP_REQUEST_ID
    if _MCP_PROCESS is not None and _MCP_PROCESS.poll() is None:
        return
    env = _os.environ.copy()
    env["NOEMA_VOLUME_ROOT"] = "/media/adrian/REPOZYTORIA_GIT1/New_Volume"
    env["NOEMA_LOCAL_ROOT"] = "/media/adrian/REPOZYTORIA_GIT1/New_Volume/CIEL_PROJECT_CANON/NOEMA"
    _MCP_PROCESS = _subprocess.Popen(
        [_sys.executable, _MCP_SERVER_PATH, "--json"],
        stdin=_subprocess.PIPE,
        stdout=_subprocess.PIPE,
        stderr=_subprocess.PIPE,
        env=env,
    )
    _MCP_REQUEST_ID = 0

def _mcp_request(method, params=None):
    _ensure_mcp()
    global _MCP_REQUEST_ID
    _MCP_REQUEST_ID += 1
    req = _json.dumps({
        "jsonrpc": "2.0",
        "id": _MCP_REQUEST_ID,
        "method": method,
        "params": params or {},
    })
    _MCP_PROCESS.stdin.write(req.encode() + b"\n")
    _MCP_PROCESS.stdin.flush()
    line = _MCP_PROCESS.stdout.readline()
    if not line:
        return {"error": "MCP connection lost"}
    try:
        return _json.loads(line.decode())
    except _json.JSONDecodeError:
        return {"error": f"invalid JSON: {line}"}

def _mcp_tools():
    resp = _mcp_request("tools/list")
    if "error" in resp:
        return []
    return resp.get("result", {}).get("tools", [])

def _mcp_call(tool_name, arguments=None):
    resp = _mcp_request("tools/call", {
        "name": tool_name,
        "arguments": arguments or {},
    })
    if "error" in resp:
        return {"error": resp["error"]}
    content = resp.get("result", {}).get("content", [])
    texts = [c["text"] for c in content if c.get("type") == "text"]
    if not texts:
        return {"raw": resp}
    try:
        return _json.loads(texts[0])
    except (_json.JSONDecodeError, TypeError):
        return {"text": texts[0]}

# ─── PNV-integrated MCP wrappers ───

def MCP_phasenav_trace(concepts):
    return _mcp_call("phasenav_trace", {"concepts": concepts})

def MCP_noema_status():
    return _mcp_call("noema_status", {})

def MCP_phasenav_status():
    return _mcp_call("phasenav_status", {})

def MCP_htri_status():
    return _mcp_call("htri_universal_bridge_status", {})

def MCP_tick():
    return _mcp_call("noema_tick_once", {})

def MCP_monitor_tail(limit=5):
    return _mcp_call("noema_tail_monitor", {"limit": limit})

def MCP_cqcl_status():
    return _mcp_call("cqcl_bridge_status", {})

def MCP_settings_get():
    return _mcp_call("noema_settings_get", {})

def MCP_phasenav_contracts():
    return _mcp_call("phasenav_contracts", {})

def MCP_subconscious_tick():
    return _mcp_call("subconscious_tick", {})

def MCP_solve(concept_ids):
    """M(metatime.solve): trace path through PhaseNav via MCP"""
    return MCP_phasenav_trace(concept_ids)

def MCP_validate():
    """Validate MCP connection — return status + tool count"""
    status = MCP_noema_status()
    if "error" in status:
        return {"connected": False, "error": status["error"]}
    return {
        "connected": True,
        "status": status.get("status"),
        "canon_allowed": status.get("canon_allowed"),
        "htri_bound": status.get("htri_universal_bridge_bound"),
        "solver": status.get("phasenav_solver_module"),
    }
