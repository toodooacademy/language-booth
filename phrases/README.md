# Language Booth – Short Phrases pack (~500 per language)

Built by `build.py` from `src/batch*.txt` (pipe-separated: topic|tier|english|vi|zh|pinyin|ja|romaji|es|note|en_gloss).
`~` inside a cell = display text~TTS text (used for Japanese kanji with ambiguous readings, e.g. 辛い → からい).
`[L]` in the English column = the language being learned (e.g. "I'm learning [L].").

## Files
- `phrases.json` – shared concepts: `{id, en, topic, tier, note?, legacyLangs?}` + topic/tier lists + schema notes.
- `vi.json zh.json ja.json es.json en.json` – `{lang, name, count, topics, tiers, phrases:[entry]}`.
- `phrases-500.csv` – review sheet (all five languages in one row, flags in `review_flags`, `needs_review=yes`).
- `review-flags.json` – `{phrase_id: {lang: reason}}` low-confidence items (also copied into entries as `review`).
- `verify-report.txt` – raw output of the verification pass (`verify.py`).
- `audio/<lang>/<gender>/<phrase_id>.mp3` (+ `.json` with text/voice/word timings) – edge-tts, 24 kHz mono 32 kbps.
- `audio-index.json` – `{"lesson": {"he"|"she": {lang: {speak: path}}}}`, same shape as `data/audio-index.json` `lesson`, only fresh clips.

## Entry shape (superset of curriculum.json phrase entries)
```
{"id": "vi-ph-hello", "concept": "ph-hello", "text": "Xin chào!", "meaning": "Hello!", "reading": "", "speak": "Xin chào!",
 "topic": "greet", "tier": 1, "note"?: "...", "legacy"?: true, "legacyAudio"?: {"he": "...", "she": "..."},
 "audio": {"he": "phrases/audio/vi/he/ph-hello.mp3", "she": "phrases/audio/vi/she/ph-hello.mp3"}, "review"?: "..."}
```
- `meaning`: English for vi/zh/ja/es; Vietnamese gloss for en (as in the existing English deck).
- `reading`: zh tone-marked pinyin (citation tones, no 一/不 sandhi marks, neutral tones unmarked); ja Hepburn romaji with macrons, particles wa/o/e; empty otherwise.
- Teacher reaction templates use `{word}`=text, `{meaning}`=meaning, `{reading}`=reading, so every entry has all three. `id` is present for the no-repeat bag.
- `text` and `meaning` are unique within each language (quiz distractors filter by meaning).
- Legacy: the 10–11 original curriculum phrases per language keep their exact text/meaning/reading/speak, flagged `legacy: true`,
  and `legacyAudio` points to their existing clips in audio/lesson/... (the old audio-index keys still resolve by speak text).

Voices (voices.json lesson): vi NamMinh/HoaiMy, zh Yunxi/Xiaoxiao, ja Keita/Nanami, es-ES Alvaro/Elvira, en-US Andrew/Ava (+2Hz).
Re-run: `python3 build.py && python3 verify.py && python3 build.py && nohup python3 gen_audio.py 8 &` (resumable; regenerates a clip only when its text/voice changed).
