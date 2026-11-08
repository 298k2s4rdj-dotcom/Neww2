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

## Mix: Alltag, Physik, Technik (3 Videos)

- `mix/kaffee/kaffee_vs_energydrink.mp4` (43,2 s), `mix/licht/schall_vs_licht.mp4` (40,4 s), `mix/eniac/eniac_vs_smartphone.mp4` (43,3 s)
- Gleiche Engine wie die Tier-Videos (`tiere/engine.py`); `mix/sources.md` (Quellen), `mix/tiktok.md` (Texte)

## Mix 2: Bauwerke, Hund, Weltall (3 Videos)

- `mix2/eiffel/eiffelturm_vs_burj_khalifa.mp4` (43,3 s), `mix2/hund/mensch_vs_hund.mp4` (38,8 s), `mix2/mond/mond_vs_erde.mp4` (35,9 s)
- `mix2/sources.md` (Quellen), `mix2/tiktok.md` (Texte)

## „Rate mal“-Serie (3 Videos)

- `ratemal/blitz/blitz_vs_sonne.mp4`, `ratemal/everest/everest_vs_marianengraben.mp4`, `ratemal/gepard/mensch_vs_gepard.mp4` (je 43,3 s)
- Jedes Video startet mit „Rate mal: …“ plus gelbem RATE-MAL-Logo und endet mit „Hast du richtig geraten?“
- `ratemal/sources.md` (Quellen), `ratemal/tiktok.md` (Texte)

## Layout

Alle Videos nutzen eine exakte 50:50-Teilung (Trennlinie bei x = 540 px). Wichtige Inhalte bleiben trotzdem aus dem rechten TikTok-Rand (140 px) heraus.

## YouTube-Branding

- `branding/youtube_profilbild.png` (800 × 800) und `branding/youtube_banner.png` (2560 × 1440), Vorschauen im selben Ordner
