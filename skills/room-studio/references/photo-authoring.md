# Creating a scene from user photos

The bundled `init` command creates an authored demo. It is not a photo reconstruction command. Photo interpretation is performed by the image-capable host agent; the compiler provides deterministic geometry for the supported semantic kit.

Inspect the actual photographs, identify visible shell, cabinets/furniture, materials, openings, and cross-image correspondences. Establish whether they show one consistent space or are design references. Keep originals unchanged. Ask for the few missing decisions that materially affect the layout, such as a scale reference, an ambiguous relative position, or permission to invent hidden surfaces.

Author the scene JSON from `catalog.demo()` as a schema example, replacing rooms and entities with the user's actual scope. Do not retain irrelevant rooms, fixed demo dimensions or furniture merely to get a render. The core validator/compiler support the semantic kinds listed in `core.py`; extend a generator for genuinely new furniture instead of disguising it as a supported shape.

Each entity has id, label, kind, room, position, rotation, params, overrides, visible and provenance. Room records have name, center, size and optional style and camera (`position`/`target` XYZ). Author cameras inside the intended space; both preview and native export use them. Scene schema/revision/style/period/environment/history/redo are required by the tools. Preserve stable IDs across revisions.

Record origin separately from geometry and scale, e.g. origin=photo_observation / user_input / inferred / designed_example, geometry=estimated / parametric, scale=user_estimate / design_dimensions / measured. A user's approval does not make an estimate measured. If no reliable pose/scale exists, label the result a photo-referenced design and make uncertain dimensions editable.

Use layout and relative relationships first, then actual geometry, then materials and lighting. Inspect the realtime preview while making edits and save each transaction. At the user's requested render checkpoint, separately render the source-facing view plus a side/reverse view, inspect the output and correct the model. Further changes make those saved images stale; they do not automatically trigger new full renders. Do not claim reliable SfM, exact recovery, physical albedo, measurement precision, collision certification or hidden geometry recovery without that separate evidence.

Private photo textures remain in the user's project. The distributed sample contains original procedural surfaces and geometric wall art, not private source photos. User-requested image assets may be generated or supplied separately with provenance; this package itself makes no external image/API calls.
