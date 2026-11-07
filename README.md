<p align="center"><b>English</b> · <a href="README.zh-CN.md">中文</a></p>

<h1 align="center">Room as Code</h1>

<p align="center"><b>Edit a room with your voice. Keep the model.</b><br>Shape a residential 3D scene in conversation. Preview locally. Keep refining.</p>

<p align="center"><a href="docs/media/room-as-code.mp4">▶ Watch the 65-second film</a> · <a href="#get-started">Get started</a> · <a href="docs/PROJECT_DETAILS.md">Technical guide</a></p>

[![A room builds up from an empty plan, layer by layer](docs/media/build-a-room.gif)](docs/media/room-as-code.mp4)

<p align="center"><sub>For Codex and Claude Code · Local preview · Editable Blender + GLB · MIT</sub></p>

## Say it. See it. Keep going.

“Extend the island forty centimetres. Move it thirty centimetres inward. Darken the top. Keep the table and wall cabinets.”

Then change your mind:

“Keep that position. Shorten it ten centimetres. Lighten the top. Make the base charcoal.”

Room as Code keeps a room as **editable scene data**: stable object IDs, dimensions, material overrides and edit history. Your assistant turns a request into a revision-checked patch. The browser previews the same saved scene; the next edit starts where the last one left off.

Use text, or **voice input supported by your host assistant**. The local viewer has no separate chat model, model API or built-in speech recognition.

**[Watch or download the complete film →](docs/media/room-as-code.mp4)** It combines actual model edits and native renders with photo references and labeled AI visualization. Commands use illustrative narration through an assistant; some model details are custom scene work. [Film provenance and formats](docs/media/README.md).

## Two homes to start from

| Manhattan apartment | Japanese three-garden house |
|---|---|
| ![Manhattan living room, native Blender daylight render](docs/images/manhattan-living-day.png) | ![Engawa and garden, actual WebGL preview](docs/images/japanese-engawa.png) |
| Nineteen modeled spaces, an open kitchen and living room, three bedrooms and supporting rooms. | Three open-to-sky gardens, tatami rooms, sliding screens and an engawa corridor. |

Both are furnished, editable design examples. They are reference-informed adaptations, with authored dimensions rather than measured surveys. For another home, work with your assistant to author or adapt a scene from photos and requirements. **This is not an automatic photo-reconstruction algorithm.**

## What stays with you

| You want to… | What Room as Code keeps |
|---|---|
| Continue a room tomorrow | A persistent scene file with stable object identities |
| Change one thing | Scoped patches with protected objects and explicit dimensions |
| Undo a decision | Saved edit history, undo and redo across restarts |
| Try a different atmosphere | Independent themes, day/night and outdoor environment controls |
| Take the model elsewhere | Editable `.blend` and `.glb` exports |

Native procedural materials stay editable in Blender. GLB uses constant PBR colors and scalar properties; procedural textures are not baked. Browser lighting and reflections approximate the native result.

## Get started

Python 3.10+ and a WebGL2 browser are enough for the bundled preview. No Python packages, npm install or model key are needed to explore the examples.

```sh
git clone https://github.com/leiyang2003/room-as-code.git
cd room-as-code
python3 preview_samples.py --port 8765
```

Open the loopback URL printed by the server. The sample selector switches between Manhattan and the Japanese three-garden house. Each launch makes fresh working copies in `runs/`; the originals stay intact. Stop the server with Ctrl+C.

### Use it with your assistant

Install the conversational skill into your working project:

```sh
python3 install_skill.py --host codex --project /path/to/your-project
python3 install_skill.py --host claude --project /path/to/your-project
```

Invoke `$room-studio` in Codex or `/room-studio` in Claude Code. Your host supplies language understanding, voice input where available, authentication and any model access. The skill, CLI helper and Claude plugin retain the compatible name **`room-studio`**.

> Inspect my-house.scene.json. Make the kitchen island 20 cm wider. Keep the dining table and every other object unchanged. Save the edit and check the result.

To create a single working scene instead:

```sh
python3 skills/room-studio/scripts/room.py init my-house.scene.json
python3 skills/room-studio/scripts/room.py serve my-house.scene.json --port 8765
```

`init` creates the bundled apartment. See [photo authoring](skills/room-studio/references/photo-authoring.md) for another home.

### Export when ready

Blender 4.2+ is required for native export and rendering. It is discovered locally, not installed automatically.

```sh
python3 skills/room-studio/scripts/room.py doctor
python3 skills/room-studio/scripts/room.py blender my-house.scene.json --out output/house.blend
```

Request a full render as a separate step. Saved render provenance detects when an image has become stale. See [inspect, undo, rendering and development](docs/PROJECT_DETAILS.md) and [native material behavior](skills/room-studio/references/native-materials.md).

## Take a closer look

- [Project and film page](docs/index.html) — portable HTML with the full film, two homes, day/night comparison and setup commands. Run `python3 -m http.server 8000` in the repository, then open `http://localhost:8000/docs/`.
- [Illustrated project guide](docs/Room_Studio_Project_Guide_EN.html) · [PDF edition](docs/Room_Studio_Project_Guide_EN.pdf).
- [Full technical guide](docs/PROJECT_DETAILS.md) · [patch operations](skills/room-studio/references/operations.md) · [validation evidence](docs/VALIDATION.md).

## Scope and license

This is an **early 0.1.0 residential design prototype**. Existing objects can be resized, moved, restyled and edited with undo/redo. New furniture families or complex custom geometry need generator work. Props are independently positioned; moving their supports requires checking them. Arbitrary external Blender changes are detected rather than silently merged.

It is not a surveyed BIM, manufacturing or construction model. Original code and documentation are [MIT licensed](LICENSE); image sources, reference rights and bundled dependencies are in [third-party notices](THIRD_PARTY_NOTICES.md). The film has [separate media terms](docs/media/README.md).
