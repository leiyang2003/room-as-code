# Native procedural surfaces

The Blender adapter has a small, versioned material layer in `scripts/native_materials.py`. It derives surfaces from the compiled primitive's role, effective theme and color; no new writable scene parameters or arbitrary patch fields are introduced. The compiler supplies a read-only `surface` profile for industrial finishes. Material recipe version 3 adds these profiles while retaining version 2 object signatures for external-edit detection.

Industrial metal replaces the previous monochrome preset. The canonical style is `industrial`; saved `mono` values remain compatible aliases. Wood-role cabinetry becomes brushed steel, frames become blackened steel, and floor/stone/wall roles become concrete. Fabric and bedding retain nonmetallic textile surfaces. Existing color overrides remain effective.

| Industrial surface | Native behavior |
|---|---|
| brushed_steel | Metalness 0.92, base roughness 0.34, anisotropy 0.55 and fine directional grain |
| blackened_steel | Metalness 0.82, base roughness 0.44, restrained directional grain |
| concrete | Nonmetallic, base roughness 0.79 and shallow procedural pores |

The ordinary role-based surfaces below remain in warm and heritage themes:

| Role | Native Blender surface |
|---|---|
| wood, frame | Anisotropic noise grain, subtle multiplication of the user color, grain roughness and shallow bump |
| floor | The same grain plus staggered 1.2 m × 0.18 m boards and 2 mm joints |
| fabric | Orthogonal weave, roughness variation, sheen and 0.4 mm bump distance |
| white with an explicit sheer marker | Fabric surface for curtains; ordinary white ceramics remain plain |
| stone | Subtle color and roughness variation with 0.22 mm pore bump distance |

These are restrained procedural approximations, not scanned materials. The chosen wood/floor bump distance is 0.35 mm. Strength settings attenuate these distances; they are shader bump, not displaced or manufacture-ready geometry. Material colors use the same effective role color from the scene, including user overrides. Grain modulation is a small multiplier around that tint. Cloth retains the explicit color without a color texture.

The kit builds geometry in metres at object scale one. Textures use local **Object** coordinates, not normalized Generated coordinates. Moving, rotating and resizing a kit entity reuses the same physical-frequency material recipe. Grain restarts in each primitive's local space; continuous grain across independently generated cabinet pieces is not promised. A role shares a material at the same color/settings, keeping the implementation and saved model small. External unapplied object scaling is outside this metric assumption and is subject to managed-transform conflict detection.

## Upgrade and incremental behavior

`MATERIAL_VERSION` participates in the procedural material cache key. Bump it whenever a recipe changes. Synchronization of an unchanged primitive replaces only a mismatched material slot; it preserves geometry and reports `updated_material_parts` separately from `updated_parts`. Subsequent unchanged synchronizations reuse the graph and mesh.

Native object signature v2 records shader node input values/settings, nodes, links, color ramps and nested group graphs as well as the existing geometry/transform state. A changed managed graph rejects synchronization before saving the master or exporting GLB. Node-editor layout is not a shading input and is excluded. Material graph digests are cached within each synchronization pass.

Older v1 masters are checked with their original signature format and must still use the known two-node Principled-to-Output material graph. Extra legacy graph nodes/links refuse migration. The old signature cannot retroactively identify scalar edits it never recorded; this upgrade does not claim to recover that history. New saves carry v2 signatures.

Renders record the material recipe version in their sidecar. A missing/different version is `STALE` with `reason=renderer_changed`, even when scene JSON is unchanged. This prevents older plain-color renders from appearing current after this adapter upgrade. Render execution is still a separate explicit action.

## GLB export boundary

The native noise/wave/brick/bump graphs are retained in `.blend`. The current GLB path does **not** bake them. It temporarily substitutes a supported constant Principled PBR material, preserving the effective linear base color, scalar roughness, metalness, alpha and other supported shader constants. It restores native slots and deletes temporary copies in `finally`, including when export fails; shared mesh data is visited once.

The validation report explicitly says `glb_surface_mode = constant PBR fallback; procedural textures not baked` and records the fallback material count. GLB therefore carries editable separate geometry and base PBR appearance, without the native grain/weave/pores. Do not present it as a texture-identical export. Baking image textures with UVs would be a separate feature.

Official references: [Blender Object texture coordinates](https://docs.blender.org/manual/en/4.2/render/shader_nodes/input/texture_coordinate.html), [Blender glTF materials](https://docs.blender.org/manual/en/4.2/addons/import_export/scene_gltf2.html#materials).

Run `blender --background --factory-startup --python-exit-code 1 --python tests/native_materials.py` for the targeted migration, persistence, incremental update, color, actual GLB data and external-node-edit checks. It does not render. Final visual quality needs the separate render checkpoint.
