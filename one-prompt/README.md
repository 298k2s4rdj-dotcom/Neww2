# ONE PROMPT

A ~4:40 min animated short film about learning AI by starting small, built with
[Remotion](https://www.remotion.dev) (React + TypeScript, 1920×1080, 30 fps).
It includes a script that uploads the film to YouTube through the YouTube Data API v3.

> *Motivation is loud. Habits are quiet.*

Black silhouette characters (MAX in a hoodie, LENA with glasses, FRIEND in a cap,
and the BOSS) with expressive white eyes, flat gradient sets, typewriter speech
and thought bubbles, serif title cards. There's no voice acting, but there is a
full score and sound design.

## Quick start

```bash
cd one-prompt
npm install          # also scans /public for optional audio
npm run preview      # Remotion Studio, scrub through the film
npm run render       # → out/one-prompt.mp4 (renders, then masters the audio)
npm run thumbnail    # → out/thumbnail.png (1280×720)
npm run upload       # → uploads to YouTube (private by default)
```

Requirements: Node.js 18+ (tested with 22). Remotion downloads its own headless
Chrome on the first render. To use a Chrome Headless Shell you already have, set
`REMOTION_BROWSER_EXECUTABLE=/path/to/chrome-headless-shell`.

## Project layout

```
src/
  config.ts            ← ALL timings (scene lengths, dialogue, beats), in seconds
  OnePrompt.tsx        main composition: scenes in order + music volume curve
  Root.tsx             registers <OnePrompt> (video) and <Thumbnail> (still)
  scenes/Scene1–6.tsx  one component per scene
  components/
    Character.tsx      silhouette rig: moods, blinking, breathing, arms, walk, sit
    Bubble.tsx         speech / thought bubbles with typewriter text
    TitleCard.tsx      black full-screen serif cards
    Sets.tsx           café, apartment, bedroom, office backgrounds
    Window.tsx         day / evening / night / morning / rain window
    WallChart.tsx      "30 DAYS TO AI MASTERY" chart, its "1 PROMPT" back side
    Screens.tsx        laptop closeups: course page, module, chat UI, notes
    Rain.tsx, Props.tsx, Shots.tsx, Sound.tsx, …
scripts/
  scan-assets.ts       finds optional audio in /public → src/generated/assets.json
  upload.ts            OAuth2 + resumable YouTube upload + thumbnail
public/
  music.mp3            the score
  sfx/                 30 sound effects / ambiences (see sfx/README.md)
```

### Tweaking timings

Everything time-related is in **`src/config.ts`**, in seconds:

- `SCENES.sceneN.duration`: change it and all later scenes shift automatically.
- Dialogue lines (`lines: [{ who, at, to, text }]`), thought bubbles, montage beats,
  the prompts/day counter steps, title card texts.
- `TITLE_CARD` (3 s), `TYPE_CPS` (typewriter speed) and `MUSIC` volumes.

Beat times are relative to the start of their scene.

| # | Time        | Scene |
|---|-------------|-------|
| 1 | 0:00 – 0:40 | Title card, café: "I'm learning AI. ALL of it.", the wall chart, the $199 course |
| 2 | 0:40 – 1:40 | Module 1 of 47, five excuses, red X's, chart crumpled into the bin |
| 3 | 1:40 – 2:20 | Title card, "1 MONTH LATER", LENA: "One prompt", chart flipped, "1 PROMPT" |
| 4 | 2:20 – 3:30 | First prompt, montage of green checks, counter 1 → 10 prompts/day (music fades up) |
| 5 | 3:30 – 4:10 | Big goal deleted, rainy night "Just one.", title card |
| 6 | 4:10 – 4:40 | FRIEND asks, MAX passes it on, final card, `@howtowithai` end card |

## Sound

The film has a full sound design. There's no dialogue audio, but everything
sounds like it does in real life:

- **Score:** `public/music.mp3`, one continuous piece with a recurring felt-piano
  melody. It is quiet and lonely while MAX gives up, warm and building in scene 4,
  and gentle in the rain. `MUSIC.levels` in `src/config.ts` sets the volume per scene.
- **Ambience:** café murmur, evening and night room tone, morning birds, office
  hum, rain with distant thunder. They change with every cut, so each place
  sounds different.
- **Foley:** footsteps, the pin, the laptop turning, typing, clicks, the message
  whoosh and reply chime, one marker squeak per red X and green check, the chart
  ripped off, crumpled, landing in the bin, unfolded and flipped, the marker
  writing "1 PROMPT", the fridge, the alarm clock, the sofa, the phone sliding
  across the table, coffee cups and MAX's sighs.
- **Automatic:** a soft pop when a bubble appears and a swell under every title card.

Every sound cue sits next to its scene, in a `SceneNSound` component in
`src/scenes/SceneN.tsx`, timed with the same config values as the picture. That
way sounds move along when you change the timings. The available files are listed
in `public/sfx/README.md`. If you replace a file with one of the same name it is
used automatically, and if one is missing it's skipped silently.
`npm run preview|render|thumbnail` rescans `/public` first.

After rendering, `npm run render` runs `npm run master` automatically. This step
normalizes the film's audio to YouTube loudness (−14 LUFS, −1.5 dBTP) with a
two-pass loudnorm, using the ffmpeg that ships with Remotion. The video stream is
copied untouched.

All audio was generated with ElevenLabs (Music v2.5, Sound Effects v2).

## YouTube upload

### 1. Google Cloud setup (one time)

1. Go to <https://console.cloud.google.com/> and create (or select) a project.
2. **APIs & Services → Library**: search for **YouTube Data API v3** and click **Enable**.
3. **APIs & Services → OAuth consent screen** (Google Auth Platform → Branding/Audience):
   - User type **External**. Fill in the app name and your email.
   - Under **Audience → Test users**, add the Google account that owns your YouTube channel.
   - Leave the app in *Testing*. Refresh tokens for apps in testing expire after 7 days,
     and the script then just asks you to sign in again.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**
   - Application type: **Desktop app**.
   - Download the JSON and save it as **`one-prompt/client_secret.json`**.

`client_secret.json` and `token.json` are in `.gitignore`. Never commit them.

### 2. Upload

```bash
npm run render                  # if not rendered yet
npm run upload                  # private (default)
npm run upload -- --public      # or --unlisted
npm run upload -- --no-thumbnail
npm run upload -- --file other.mp4 --thumbnail other.png
```

On the first run a browser opens the Google consent page. Pick your channel's
account and allow access. The token is stored in `token.json` and reused next time.
The upload is **resumable**: 8 MB chunks with a progress bar, and if the connection
drops it asks the server for the last received byte and continues from there.

Metadata: title *"ONE PROMPT | An Animated Short Film About Learning AI"*, the
description and tags, category 1 (Film & Animation), language `en`,
`selfDeclaredMadeForKids: false`. Edit `METADATA` in `scripts/upload.ts` to change them.

After the upload, the script renders `out/thumbnail.png` if it is missing and sets
it with `thumbnails.set`. Custom thumbnails only work on phone-verified channels
(<https://www.youtube.com/verify>). If that fails, the video stays uploaded and you
get a warning. At the end it prints the video URL.

> Note: videos uploaded through an API project that hasn't passed Google's audit
> may be locked to *private* by YouTube no matter what privacy setting you request.
> You can then make them public by hand in YouTube Studio.
