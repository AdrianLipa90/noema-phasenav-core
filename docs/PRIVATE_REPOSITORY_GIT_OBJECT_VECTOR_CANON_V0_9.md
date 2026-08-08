# Private Repository Git-Object Vector Canon v0.9

## Purpose

This layer begins vectorization of every repository visible as `private` under the authenticated `AdrianLipa90` GitHub installation while removing human-label and hand-weight arbitrariness from the routing parent.

The inventory rule is mechanical:

`visibility == private`

Archived repositories are retained in the inventory. They are not silently discarded. A repository with no Git head receives no invented routing vector.

## Canonical vector parent

A repository snapshot vector is derived only from the native Git commit object digest at the repository's default-branch head.

Repository name, GitHub repository id, default-branch name, repository size, manually assigned importance, topic labels, and file-path strings are provenance metadata only. None is a vector parent.

For files and directories the same rule generalizes:

- file state -> native Git `blob` digest;
- directory state -> native Git `tree` digest;
- repository/history state -> native Git `commit` digest;
- annotated tag state -> native Git `tag` digest.

Git already domain-separates object types when it constructs object ids. PhaseNav therefore does not add a second human-label hash to distinguish them.

## Phase law

For a native Git object digest interpreted exactly as integer `N_git`, coordinate `i=0..35` is

`phi_i = (N_git * (i+1) * ln(2)/12) mod 2pi`.

The `ln(2)/12` increment is the same information-phase increment used by the existing PhaseNav high-precision non-numeric route. The difference is the parent: v0.9 consumes the Git content identity directly and does **not** call `M_collatz_hash(repository_name_or_path)`.

The digest is not first re-hashed with a PhaseNav-specific or project-name-specific function.

## Edges do not get invented vectors

Import, dependency, containment, parent/child, and other graph relations are represented by their actual endpoint Git objects plus typed edge metadata. An edge label is not converted into a new pseudo-object vector.

Distance, Berry connection, edge weight, and holonomy may be computed from endpoint vectors using the existing PhaseNav operators. Those measurements describe the declared content graph; they do not prove the semantic or scientific truth of an edge.

## Snapshot 2026-08-08

The first private-repository inventory contains:

- 40 private repositories;
- 39 repositories with a real Git head and therefore a 36D repository-state vector;
- 39/39 distinct routing-vector SHA-256 identities;
- one archived empty repository (`noema-poincyre-cymatix`) with no invented vector.

Inventory SHA-256:

`d47ace603e52fdb3fbe77556b370ac272d4ac5f3d0232b0bda4fbc998a05ab70`

Vector-set SHA-256:

`a7e458063b3fb94d817f132c3c4dceee5a6ed7ade32237bec4acaff392640e0b`

## Epistemic boundary

This is content/provenance routing canon. It does not claim that two nearby repository vectors are semantically equivalent, that a repository is scientifically correct, or that a dependency is physically real.

`vectorization -> scientific promotion` remains forbidden.

The next descent is deterministic: obtain Git trees/blobs from each frozen repository head, vectorize those native objects with the same digest-native operator, then build import/dependency/containment edges from parsed repository evidence. No hand-assigned semantic weights are required.