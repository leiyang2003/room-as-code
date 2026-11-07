# Validation and evidence

The public repository was prepared from the validated 0.1.0 source archive, then checked again in its independent publication directory. Runtime scene/compiler/viewer source is retained; publication changes cover documentation, packaging and portable development checks.

## Recorded project acceptance

These are historical acceptance records from the development workspace, not newly claimed reruns in the public checkout:

| Area | Evidence | Scope |
| --- | --- | --- |
| Codex and Claude Code | [Codex](validation/codex-edits.json), [Claude](validation/claude-edits.json) | Each host actually moved/rotated a sofa and raised/recolored wall art in an installed skill fixture; independently compared all saved entities and material overrides; fresh-process undo/redo. One fixed task per host. |
| Full native apartment | [Native result](validation/final-native-results.json) | 251 entities, 2,211 compiled parts, 2,189 meshes. Local edits protected unrelated matrices and fingerprints; undo, native save/reopen and GLB reimport passed. No rendering during edits. |
| Final images | [Visual review](validation/final-visual-results.json) | Four actual Blender renders: living day/night, bedroom day and overview. SHA-256 values identify the original renders. Public copies in `docs/images/` have identifying PNG metadata removed without changing compressed pixel data; their new hashes are recorded in publication results. Prototype quality and export limitations are recorded explicitly. |

The native acceptance ran with Blender 4.2.23 LTS. A fixed integration task does not prove arbitrary language understanding or photo reconstruction. Host wall time includes model and service waiting; it is not local patch execution time. GLB checks prove geometry and basic PBR export, not procedural texture equivalence.

## Publication checks

[Publication results](validation/publication-checks.json) record checks run against the clean publication copy: the complete Python unit suite, both fresh project skill installations, scene initialization/compilation, frontend build and the browser suite. These checks are separate from the historical host and full native results above.

Run the commands in the root README to repeat them. `examples/manhattan.scene.json` is the current furnished apartment. `examples/kit-grid.scene.json` and its compatibility alias `quiet-house.scene.json` are the historical component-grid fixture used by smaller integration checks.

Private photos, third-party reference PDFs, personal filesystem paths, raw host logs, installed dependencies and internal coordination documents are excluded from this repository. The original source archive SHA-256 was `9e02609f7b91c21c0f71d752f113bb447c67cb46c32b1bd13c6d8cedb804280e`; the public copy has its own manifest because its documentation and packaging differ.

## Industrial Metal update

The updated local unit suite contains 38 tests, including legacy mono compatibility, physical finish selection, unchanged layout/color overrides, undo and protection against surface-only changes. Browser undo/redo was exercised against the updated live preview with no page errors or horizontal overflow. [Preview capture](images/industrial-metal-preview.jpg).

[Native industrial result](validation/industrial-native-results.json) verifies Blender 4.2.23 shader creation, native save/reopen and constant-PBR GLB metalness/roughness, without image rendering. Repeat with `blender --background --factory-startup --python-exit-code 1 --python tests/native_industrial.py`.

Native material version is now 3. The full-apartment and rendered-image evidence above remains historical 0.1.0 acceptance; no new complete apartment render is claimed for this theme update.

## Two residential samples (current main)

`validation/samples-checks.json` records the dual-sample integration checks. `tests/samples-browser.mjs` uses real Chromium WebGL2, changes Japanese sliding-screen geometry, changes Manhattan curtain geometry, verifies that each edit leaves the other sample file intact, switches and reloads saved state, checks roof visibility, and checks both layouts at 390px. Invalid sample IDs are rejected. The original single-scene browser test remains supported.

The Python suite now contains 48 tests, including Japanese layout, three open-to-sky gardens, entry connectivity, protected edits, reversible changes, and two-leaf screen geometry. The fresh public-runtime Japanese Blender export reports 241 entities, 3,033 meshes and material recipe version 3. This is native export evidence, not a new full image render or a new Codex/Claude Code host execution. Japanese images are browser captures; Manhattan images retain their previously documented native-render provenance. Third-party floor-plan drawings and private reference files remain excluded.
