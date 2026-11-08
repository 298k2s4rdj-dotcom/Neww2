# Jelly Beans – Shorts

## The Girl on Route Nine (test Short)

- `shorts/girl_on_route_nine.mp4`: 1080x1920, 30 fps, 43.6 s, H.264 + AAC
- `src/render.py`: draws and animates every frame procedurally (silhouettes, rain, fog, flicker, lightning, camera moves) with Pillow/NumPy, then muxes with ffmpeg
- `src/narration_raw.mp3`: the narration, from the ElevenLabs voice "Jack – Deep Dark Horror Narrator" (voice only)

Re-render: `python3 src/render.py` (needs numpy, Pillow, ffmpeg).

## Erde vs. Sonne (deutsches Vergleichsvideo)

- `erde_vs_sonne/erde_vs_sonne.mp4`: 1080x1920, 30 fps, 44,2 s, H.264 + AAC
- `erde_vs_sonne/render.py`: zeichnet und animiert alles prozedural (Pillow/NumPy), synthetisiert die Soundeffekte, muxt mit ffmpeg
- `erde_vs_sonne/audio_raw/`: Sprecher-Audio pro Szene von ElevenLabs (Stimme „Jan – Social Media Creator“, eleven_multilingual_v2) und Wort-Zeitstempel (ElevenLabs Scribe)
- `erde_vs_sonne/sources.md`: alle Zahlen mit Quellen · `erde_vs_sonne/tiktok.md`: Beschreibung und Hashtags

Neu rendern: `python3 erde_vs_sonne/render.py` (QC-Bilder: `--stills`).

## Tiere vs. Mensch (3 Videos)

- `tiere/blauwal/blauwal_vs_mensch.mp4` (43,3 s), `tiere/giraffe/giraffe_vs_mensch.mp4` (40,0 s), `tiere/elefant/elefant_vs_mensch.mp4` (39,5 s): 1080x1920, 30 fps, H.264 + AAC
- `tiere/engine.py`: gemeinsame Animations-Engine (Split-Screen, Punktestand, Zähler, wortgenaue Untertitel, synthetische Soundeffekte)
- `tiere/<tier>/render.py`: Szenen und selbst gezeichnete Figuren; `audio_raw/`: ElevenLabs-Stimme pro Szene + Scribe-Zeitstempel
- `tiere/sources.md`: alle Zahlen mit Quellen · `tiere/tiktok.md`: Beschreibungen und Hashtags

Neu rendern: `python3 tiere/<tier>/render.py` (QC-Bilder: `--stills`).
