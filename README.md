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
