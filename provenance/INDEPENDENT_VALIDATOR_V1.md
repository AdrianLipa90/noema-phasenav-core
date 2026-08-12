# Independent PhaseNav Validator v1

## Status

`IMPLEMENTED / SOURCE_SYNTAX_VERIFIED / FULL_REPOSITORY_EXECUTION_PENDING`

Branch: `validator/independent-v1`

## Motivation

GitHub Actions for current `master` are presently blocked before runner allocation by an account billing/spending-limit condition. A red Actions badge therefore cannot currently distinguish repository failure from CI infrastructure failure.

This validator creates a validation path that does not depend on GitHub Actions and does not trust PhaseNav's own validation helpers for its primary evidence.

## Independence model

Layer A is standard-library-only and inspects repository artifacts directly:

1. repository structure and executable surfaces;
2. Python source syntax;
3. canonical seed ledger parsed from AST without importing PhaseNav;
4. canon manifest JSON syntax;
5. NPY header, shape, dtype-derived payload size and row count without NumPy;
6. every crystal metadata JSONL record and row-count equality;
7. anti-regression AST/source checks for silent broad exceptions, 36D→11D truncation, zero-padding and placeholder operators;
8. import-time mutation guard for `pnv_runtime._init`;
9. active-crystal documentation consistency.

Layer B is an isolated subprocess runtime probe. It imports the package and checks 36D runtime invariants using a temporary empty runtime directory. Its failure cannot suppress Layer A findings.

## Output contract

Per-check statuses: `PASS`, `FAIL`, `SKIP`.

Overall exit code is zero only when no check is `FAIL`.

Optional JSON receipts contain validator SHA-256, critical artifact hashes, per-check evidence, Python version and verdict counts.

## Validation boundary

The validator source was syntax-compiled independently before commit. A full checkout execution is still required before changing this record to `EXECUTED_PASS` or `EXECUTED_FAIL`.

No scientific claim is validated or promoted by this tool.
