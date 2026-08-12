# concept_phases

Executable canonical concept-phase surface.

Files:
- `catalog.py` — in-memory records backed by `canon.cards`;
- `export.py` — JSONL exporter;
- `__init__.py` — import surface.

Every exported concept carries an explicit 36D `phase_vector_36d`. Missing historical
`glossary.pnv` is not treated as an empty concept universe.
