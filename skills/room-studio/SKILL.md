---
name: room-studio
description: Create and edit residential 3D scenes from photos or text in Codex or Claude Code, with persistent scene data, parametric furniture, independent styles and day/night lighting, browser previews, and Blender/GLB exports. Use for room creation, conversational layout changes, reskinning, curtains, wall art and lighting; not surveying or arbitrary mesh repair.
---

# Room Studio

Use conversation to author and maintain an editable residential scene. Keep scene state on disk; use the bundled scripts for validated transactions and exports. The installed skill directory contains `scripts/`, `references/`, and `assets/`. Resolve helpers relative to this file, and create the user's scene outside the installation directory.

## Start or resume

1. Inspect the user's project for an existing `*.scene.json` and its exported master before creating anything. Read its revision and entities with `python3 <skill>/scripts/room.py inspect <scene>`.
2. Run `python3 <skill>/scripts/room.py doctor`. Reuse an existing Blender installation; `BLENDER` may point to its executable. Do not install or download Blender merely because `/Applications/Blender.app` is absent.
3. For the bundled residential example, run `python3 <skill>/scripts/room.py init <new-scene.json>`. It creates the current authored residential demonstration with design dimensions; the historical eight-room example remains a separate fixture. For user photos or a different home, read [photo-authoring.md](references/photo-authoring.md), inspect the images, and author/adapt the scene to those references. The demo is not a reconstruction of the user's photos.
4. Start the preview with `python3 <skill>/scripts/room.py serve <scene> --port <available-port>`. Open the reported loopback address in a real browser when available. The preview has no cloud/model API; language understanding happens in this conversation.

## Make a conversational edit

Read [operations.md](references/operations.md) for the exact transaction contract. Resolve the user's intent to stable entity IDs, SI dimensions, explicit scope, and protected objects. Inspect candidates when "this" or "that" is ambiguous; ask only for information necessary to avoid changing the wrong thing.

Identify objects using the stable `id`, `label`, room, and optional `detail` / `semantic_group` from `inspect`; read `provenance` when source or scale matters. `kind` is the base geometry family, not a complete item description: `kind=art` can represent wall art, a `table_setting`, `ceramic_vessel`, `tea_service`, or `toiletries`. Do not classify all `art` entities as wall pictures or apply wall-attachment assumptions to tabletop objects. Preserve the existing detail and grouping when moving an item. These are read-only identification fields in the current patch protocol; do not add `detail`, labels, provenance, or arbitrary fields to `set` or `params` to bypass validation.

Write a reviewable patch JSON with the current `expected_revision`, a short human-readable label, and supported operations. Include explicitly protected object IDs in `protect`. Read current XYZ, rotation, dimensions and overrides from disk; translate relative distances to absolute metres, and preserve axes the user did not mention. Copy the position array programmatically and change only the requested indices; do not retype or round untouched coordinates, even for display-sized decimal noise. For fixed decorations (art, mirror, curtain, hidden light), edit that entity, keeping its attachment plane unless the user asks to change it. "Left" in a camera view is ambiguous without that view's orientation; resolve the intended world direction before applying. Run `apply ... --dry-run` when a broad edit or dependencies warrant inspection, then `apply`. Never treat a tool failure as success. A revision conflict requires rereading and reconsidering the patch, not silently changing its revision.

Changes to an island's width regenerate its counter/sink subparts from parameters. Material overrides survive theme changes. Room theme overrides survive a global theme change. Curtain openness changes actual pleated geometry. Day/night and outdoor environment are independent. Hidden light diffusers have actual light sources.

The browser reads the same scene file and updates automatically. Inspect the resulting `changed` IDs and field diffs, reread the saved scene, and verify protected objects and existing material overrides. Only claim visual verification if the preview was actually inspected. Use `undo` and `redo` for reversible corrections; in a new conversation, resume from the saved scene and its revision/history. For a different operation not supported by the current kit, extend the scene/compiler narrowly and validate actual behavior; do not write arbitrary fields and claim they affected geometry.

## Native model and visual verification

During iterative edits, apply transactions, save scene state, and inspect the realtime browser preview. Do not automatically run a full Blender render after each change. Batch the user's edits; render only when the user requests it or reaches an agreed final checkpoint.

For a requested native export without full rendering, run `python3 <skill>/scripts/room.py blender <scene> --out <master.blend>`. For the separate final render step, run `python3 <skill>/scripts/room.py render <scene> --out <master.blend> --image <image.png> --room <room-id|overview>`. It synchronizes once, exports the master/GLB, then renders. It preserves unchanged managed primitives and refuses detected external edits to managed mesh/material/root properties. Do not delete or overwrite a conflicting master to force synchronization; use a separate output and explain the conflict.

The native adapter adds versioned wood/floor grain and fabric/stone micro surfaces while preserving effective color overrides. Older known plain materials upgrade through material slots without rebuilding unchanged meshes. Node-graph changes are included in conflict checks. GLB currently receives an explicit constant PBR fallback, preserving colors and shader constants but omitting procedural texture detail; no automatic baking occurs. See [native-materials.md](references/native-materials.md). Saved renders from a different material version are STALE (`renderer_changed`) and need the separate render step before being presented as current.

Inspect browser geometry during editing; inspect actual render images after the separate render step. Check intended objects and protected objects, not merely command exit codes. Each new render has a `.render.json` sidecar with scene hash/revision and image hash; `render-status <scene> <image>` reports CURRENT / STALE / MISSING with a reason. Check status after rendering too: a scene edited while Blender was running makes that image stale. Undo can restore identical content at a newer revision, in which case the matching image is CURRENT. After further edits, do not present an old render as current. The browser uses approximate transmission, reflections and indirect lighting; native Blender renders are a separate result. A successful CLI test does not establish successful host execution. Verify each claimed host separately. Distinguish host/model waiting time from script execution time when reporting performance.

## Sample visual direction and evidence

The supplied home uses warm wood, light plaster, glass and metal; themes include warm, monochrome and heritage. The example's fixtures are recessed or concealed; avoid adding exposed ceiling lamps to it unless requested. Other user projects follow their own design direction.

Maintain source and scale distinctions. A photo observation, a user estimate, an approved inference and an actual measurement are different facts. New unseen rooms and the original programmatic window scenery are design examples. Preserve user photos locally; no public upload or deployment is implied by creating or editing a scene. Keep private photos out of a distributable example.

Report the changed objects, preview/native artifacts, actual validation and material limitations. Preserve unrelated files and existing work.
