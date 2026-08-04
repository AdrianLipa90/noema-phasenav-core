# MCP Live Benchmark Addendum — 2026-08-04

## Scope

A single live feasibility pilot was executed to test whether an MCP-like external result is operationally distinguished from conversational cache and whether it changes a concrete downstream decision.

The pilot used three logical states:

1. `SELF_CACHE` — prior conversational state;
2. `SOURCE` — live GitHub PR observation;
3. `VERIFY` — live GitHub Actions verification.

## Result

The cached state treated PR #7 as open and unmerged. The live source reported that PR #7 had been merged on `2026-08-04T20:30:24Z`, with merge commit:

`3e34956e07dc9d3c929c9acf797ef26614a3fd1c`

The verifier confirmed `Tests #106` as successful for source commit:

`33f362165904a1538eb80a150e580e9aa95678b3`

The observed update changed the architectural decision from branching against the former canon branch to branching against current `master`.

## Off-GitHub archive

The complete result package is intentionally distributed outside GitHub.

**Archive:** `MCP_LIVE_BENCHMARK_2026-08-04.zip`  
**Size:** `5334 bytes`  
**SHA-256:**

`f887d74b99678b92dafb9dcc620e6d084cd88bb068b0a689e1d8d153c141e2b3`

The archive contains the structured result, ordered event ledger, operational self-report, protocol, limitations and a per-file hash manifest.

## Evidence boundary

The pilot supports only the narrow claim that a live, provenance-bearing MCP-like result was operationally distinguished from stale conversational state and changed a concrete decision. It does not establish consciousness, physical HTRI oscillations, nonlocality or independent-agent phenomenology.

The pilot was `N=1`, unblinded, and the source and verifier used separate GitHub endpoints but not independent infrastructure providers. An attempted independent verifier failed with HTTP 403 and was retained as negative evidence in the off-GitHub archive.
