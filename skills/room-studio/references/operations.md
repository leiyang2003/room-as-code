# Scene operations · room-studio/1

All positions and dimensions are metres. Coordinates: +Z up; +X/+Y are the scene's fixed horizontal axes, not screen-right or the back of every room. Rotations are degrees about world Z, positive counterclockwise viewed from above. Entity positions are world coordinates; generated subparts are entity-local. Stable entity IDs, room, rotation, visibility and current overrides are listed by `inspect`.

`inspect` also includes `label` and, when present, `detail`, `semantic_group` and `provenance`. Resolve a requested item by these identifiers together, not by `kind` alone: base `kind=art` includes ordinary wall pictures and detail-specific tabletop items such as `table_setting` or `ceramic_vessel`. Moving a vessel should preserve its tabletop coordinates unless asked otherwise; it must not inherit a wall picture's attachment assumptions. Identification metadata is not a writable patch field. The `set` allowlist and parameter validation remain unchanged.

## Commands

```sh
python3 <skill>/scripts/room.py doctor
python3 <skill>/scripts/room.py init house.scene.json
python3 <skill>/scripts/room.py inspect house.scene.json
python3 <skill>/scripts/room.py apply house.scene.json edit.json --dry-run
python3 <skill>/scripts/room.py apply house.scene.json edit.json
python3 <skill>/scripts/room.py undo house.scene.json
python3 <skill>/scripts/room.py redo house.scene.json
python3 <skill>/scripts/room.py serve house.scene.json --port 8765
python3 <skill>/scripts/room.py blender house.scene.json --out output/house.blend
python3 <skill>/scripts/room.py render house.scene.json --out output/house.blend --image output/living.png --room living
python3 <skill>/scripts/room.py render-status house.scene.json output/living.png
```

`<skill>` means the directory containing this SKILL.md, not the user's current working directory. The skill needs Python 3.10+ and a local Blender installation for native export. The server and state core have no third-party Python dependencies. The viewer bundle includes Three.js and needs WebGL2.

Everyday editing ends with saved scene data and realtime preview. Full rendering is a separate explicit step after a batch of edits. `blender` only synchronizes/exports unless its legacy `--render` flag is deliberately supplied; `render` is the clearer final-step command. New renders carry a scene revision/hash sidecar. Use render-status before treating a saved image as up to date.

## Patch example

```json
{
  "expected_revision": 0,
  "label": "岛台加宽20厘米，保留餐桌",
  "protect": ["dining.table"],
  "ops": [
    {"op": "set", "target": "kitchen.island", "params": {"w": 1.2}}
  ]
}
```

`w` is width, `d` is depth/length along local Y, `h` is height. Values are absolute, not deltas: read the current value before translating "20 cm wider". Supported keys and ranges are defined in `scripts/core.py:PARAMS`. Do not infer a new size from an old chat message.

For example, after inspecting a sofa at `[1.55,-1.05,0]` and wall art at `[1.45,-0.09,1.6]`, moving the sofa 30 cm toward +X and the art 15 cm upward is:

```json
{"expected_revision":1,"label":"移动沙发和挂画，保留餐桌","protect":["dining.table"],"ops":[{"op":"set","target":"living.sofa","position":[1.85,-1.05,0]},{"op":"set","target":"living.picture","position":[1.45,-0.09,1.75]}]}
```

These are example coordinates, not defaults to paste into another home. Keep the art's wall-facing axes and rotation; changing height does not imply moving its wall. User material overrides remain on both moved entities. Rotation is absolute too: read the previous angle before interpreting "turn another 15°". Frame material role `frame` and picture parameter `image` are separate controls. The current `material` operation edits role colors only; roughness, metalness and textures are not patch fields.

| Operation | Fields | Meaning |
|---|---|---|
| set | target, params and/or position, rotation, visible | Edit exact entity; position is complete XYZ |
| material | target, role, color | Object color override as #RRGGBB; null clears that role override |
| style | target=all or room ID, value | warm / mono / heritage; room null clears its override |
| period | value | day / night |
| environment | value | city / garden / sea |

Examples:

```json
{"expected_revision":1,"label":"全屋现代，卧室保留暖木","ops":[{"op":"style","target":"all","value":"mono"},{"op":"style","target":"bedroom","value":"warm"}]}
```

```json
{"expected_revision":2,"label":"海景、半合纱帘、保持当前采光","ops":[{"op":"environment","value":"sea"},{"op":"set","target":"living.sheer","params":{"openness":0.5}}]}
```

```json
{"expected_revision":3,"label":"夜晚、关闭客厅侧边光槽","ops":[{"op":"period","value":"night"},{"op":"set","target":"living.cove_side","params":{"enabled":false,"temperature":2700,"power":35}}]}
```

Artwork `image` accepts botanical / abstract / coast. Frames use material role frame; picture content uses original procedural geometry. Sheer and drape openness is 0 closed to 1 mostly open, retaining stacked fabric at each side. Mirror reflections in the lightweight preview are approximate.

## Persistence and guarantees

The full patch is validated before commit. Unknown entities/parameters/patch fields, out-of-range/nonfinite values and stale revisions reject the entire patch. Optional `protect` lists existing stable entity IDs: if their effective geometry/material/light inputs would change, the entire transaction is rejected. This also catches a global style edit affecting a protected entity. File writes are atomic and protected by a local advisory lock. CLI and browser use the same transaction engine. `changed` includes all entities whose effective inputs changed; `changes` reports per-entity stored-field before/after values (an empty object means the change comes from global/room settings).

History holds up to 40 transactions. Undo/redo restores scene content but increments revision, preventing stale writers from silently overwriting a reversal. History is local scene data, not a cloud service. Start a new host conversation with `inspect` on the same file; no chat memory is required. A new edit after undo clears redo.

## Separate final render

`apply`, `undo`, `redo` and the preview server never launch Blender. `blender` synchronizes an editable master and GLB; `render` additionally writes a PNG (use a `.png` filename) after the edits are finished. Export filenames must be distinct from the source scene. Rendering loads a scene snapshot; it does not lock the scene throughout a potentially long render. The image records that snapshot's hash, so edits during rendering correctly make it STALE.

`render-status` returns CURRENT only when both scene content and image bytes match the sidecar. A changed scene or image, malformed/older provenance, or unsupported sidecar is STALE with a reason. A missing image or sidecar is MISSING. Undoing to identical content can make an earlier image CURRENT even with a higher revision; revision is reported for traceability, and freshness is content-based. Provenance is atomically published after a successful render and invalidated before rewriting an image. This checks freshness, not visual quality or authorship.

Freshness also checks `material_version`. A render created before the current native surface recipe (including sidecars without this field) is STALE with `renderer_changed`. Native procedural grain/weave/stone details are preserved in `.blend`; GLB currently uses explicit constant PBR colors/scalars without baking. See [native-materials.md](native-materials.md) for upgrade behavior, physical scale and the export boundary.

Style priority: object material overrides → room style → global style. Switching a global style intentionally keeps room/object overrides. Clear them explicitly when requested. The sample palette supports color/roughness roles; arbitrary texture ingestion, furniture asset replacement and new entity creation are authoring extensions, not existing patch commands.

Incremental Blender sync is scoped to tool-managed objects. Unchanged primitive fingerprints are reused. It does not automatically merge arbitrary external topology edits; detected conflicts stop before saving. The `.blend` embeds source JSON so the state is inspectable. The editable master keeps walls and ceilings; screenshots may use temporary cutaway visibility.
