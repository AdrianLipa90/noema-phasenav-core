# Git Tree/Blob Vector Canon v0.10

## Scope

v0.9 removed repository-name/branch/id/size seeds from private repository head vectors. v0.10 descends from frozen commit heads into the actual Git object database without introducing a hand-maintained file list.

## Discovery

The scanner uses Git itself:

- `git rev-parse <revision>^{commit}`
- `git rev-parse <revision>^{tree}`
- `git ls-tree -r -t -z --full-tree <revision>`

This discovers every tracked tree/blob/gitlink occurrence reachable through the selected tree. Untracked filesystem content is excluded because it has no Git object identity in the frozen source state.

## Vector parent

Every object is routed through the v0.9 digest-native operator:

- commit -> native commit digest;
- tree -> native tree digest;
- blob -> native blob digest;
- gitlink -> referenced native commit digest.

A path is an occurrence/localizer only. File name, extension, mode, path length, file size and manually assigned importance do not seed or weight the 36D vector.

Two occurrences of the same blob share one object vector. A pure rename therefore preserves the blob vector while changing the enclosing tree and subsequent commit state. A content change changes the blob digest and therefore forces a new vector.

## Graph

The scanner records only relations already present in Git:

`commit -> root tree`

and

`tree -> child object`.

Relation labels are typed metadata, not pseudo-object vector seeds. PhaseNav angular distance, Berry connection and edge weight are calculated from the actual endpoint object vectors.

Those geometric quantities identify the routed Git graph. They do not prove semantic dependency, scientific truth or causal meaning.

## Frozen-head gate

The v0.9 private snapshot freezes 39 real private-repository heads. A canonical tree/blob scan must match the frozen native head SHA exactly. Moving-head drift fails closed.

A complete private object-graph receipt requires all 39 frozen real-head checkouts. A partial scan may be used operationally but cannot claim `complete_snapshot=true`.

## Validation

Focused synthetic Git validation: `PASS_13_OF_13`.

Validated invariants include:

- native Git discovery, no manual file list;
- identical bytes in two paths -> identical blob digest/vector;
- pure rename -> blob vector invariant, tree/commit changed;
- one-byte content change -> blob vector changed;
- untracked file excluded;
- explicit commit->root-tree and tree->child edges;
- no relation-label/path edge vector;
- deterministic receipt;
- exact frozen-head gate;
- moving-head rejection;
- 39 frozen real heads;
- archived empty source has no frozen head;
- partial 39-repository aggregate cannot claim completeness.

The complete 39-checkout private tree/blob execution is currently `NOT_RUN` because those private checkouts are not exposed as local Git object databases in this execution surface. This is an execution-state limitation, not a reason to replace Git discovery with path heuristics.