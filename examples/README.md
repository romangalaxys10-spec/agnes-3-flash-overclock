# Synthetic offline fixtures

These files only demonstrate CLI usage. Repeated words are deliberate test
fixtures, not good prose, real model outputs or recovered benchmark evidence.
`draft.txt` passes T1; `rewrite.txt` with `source.txt` passes T5/custom constraints;
`editor.txt` passes T2 after explicit final extraction.

`proof-delivery.json` is a work-only synthetic proof-envelope example. Its
manifest hashes correspond to the shipped `proof-artifacts/note.txt` and
`verify.log`; code and visual proof are explicitly not applicable. The command
can be replayed from repo root. It is not recovered benchmark evidence.
