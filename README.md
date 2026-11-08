# Jelly Beans – Shorts

## The Girl on Route Nine (test Short)

- `shorts/girl_on_route_nine.mp4`: 1080x1920, 30 fps, 43.6 s, H.264 + AAC
- `src/render.py`: draws and animates every frame procedurally (silhouettes, rain, fog, flicker, lightning, camera moves) with Pillow/NumPy, then muxes with ffmpeg
- `src/narration_raw.mp3`: the narration, from the ElevenLabs voice "Jack – Deep Dark Horror Narrator" (voice only)

Re-render: `python3 src/render.py` (needs numpy, Pillow, ffmpeg).
