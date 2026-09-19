# Candidate working runtime policy v0.1

Status: `CANDIDATE_POLICY / ACTIVE_WORKING_ROUTE`

Date: 2026-09-11

This policy records the approved distinction between a working candidate and a failed/quarantined component.

```text
CANONICAL   -> admitted=true, executable=true, canonical_default=true
CANDIDATE   -> admitted=true, executable=true, canonical_default=false
QUARANTINED -> admitted=false, executable=false
FAILED      -> admitted=false, executable=false
```

A candidate is therefore not dead code. Candidate components are valid inputs to explicit working routes, tests, benchmarks and evidence generation. Every result produced through a candidate route must preserve its candidate provenance.

The runtime helper is:

`src/ciel_geometry/phasenav/candidate_runtime.py`

It deliberately does not auto-promote candidate results, modify canonical defaults, or erase prior failed/rejected evidence.

The first registered consumer for this policy is the PNCS 600-cell S3 angular carrier candidate v0.1. That carrier is callable as a candidate surface while its physical binding and canonical promotion remain open.
