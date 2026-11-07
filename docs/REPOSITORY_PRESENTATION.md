# Repository presentation refresh

## Problem and evidence

The repository opens with a technical overview and one still render. The completed 65-second film is not in the repository, voice-assisted editing is difficult to discover, and the viewer's burgundy interface differs from the requested Web Companion visual direction.

References inspected on 7 November 2026: Web Companion's paper/ink/vermilion design tokens, landing-page CSS and actual landing screenshot (the product is [anone.life](https://www.anone.life/)); the [One-Trillion Persona](https://github.com/anone-life/one-trillion-persona) README and public repository metadata. These are design and information-architecture references. Their characters, artwork, branding, fonts and product code are not imported.

## Plan

1. Add a web-encoded copy of the approved final film, a poster and a short assembly GIF. Keep its full 65-second edit and audio; strip container metadata. Link to the actual MP4 from the repository front page.
2. Reorganize the README around the product experience, voice-assisted workflow, two example homes and a short quick start. Preserve the longer technical material in a linked document; add a Chinese README.
3. Create a portable project/film page in `docs/index.html`. Use a dark cinematic opening, actual project images, native video controls, warm paper sections, system serif/sans fonts, fine rules and restrained vermilion actions. Include working English/Chinese text, a day/night comparison and copyable setup commands.
4. Apply the same shared tokens to the existing local 3D viewer, retaining its selectors, scene editing behavior and controls. The viewer's tiny asset allowlist needs to include the new local token stylesheet.
5. Check video decoding and duration, desktop/mobile/dark-mode layouts, page interactions, existing unit and browser checks, local links and Git changes. Commit and push only the intended project changes using existing authenticated Git access.

## Scope

This is a repository presentation and viewer styling update. It does not deploy a hosted service, change scene geometry, regenerate the film, or add a built-in speech-recognition service. Voice input is supplied by the user's host assistant. The film contains custom authored model work and clearly labeled AI visualization; the repository remains an early design prototype.

## Verification results

Implemented: English and Chinese README; full-length web-encoded film, GIF and poster; portable bilingual project page; shared paper/ink/vermilion tokens; refreshed viewer styling. The longer original technical text is retained in PROJECT_DETAILS.md.

Verified locally: 48 Python tests; reproducible frontend bundle; actual WebGL scene navigation, styles, room lighting, curtains, undo/redo and saved state; both residential samples and isolated sample edits; 390px layouts; bilingual project copy, clipboard, day/night images, image proportions, reduced motion, native video playback and pause. The published video decodes completely and retains 65 seconds / 1,560 frames / 24 fps / 1600×900 / 48 kHz stereo. No page errors or missing assets were observed. Machine results are in `docs/validation/presentation-checks.json`; generated screenshots/logs stay under ignored `docs/qa/`.

Release packaging: source and standalone skill archives rebuilt and verified by CRC, per-file hashes, private-file exclusion, clean extraction, Codex/Claude installation and fresh example compilation. The source archive includes both READMEs, the project page and film; the standalone skill includes its local shared token stylesheet. Remote GitHub verification follows the commit.
