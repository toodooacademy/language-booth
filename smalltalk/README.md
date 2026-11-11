# Language Booth — Small Talk (200 topics × 5 languages)

Build:   python3 build.py      (src/batch*.py -> topics.json, <lang>.json, smalltalk-200.csv, review.json)
Verify:  python3 verify.py     (pinyin vs pypinyin, romaji vs pykakasi, punctuation, ¿?/¡! -> verify-report.json)
Audio:   nohup python3 audio.py 4 &   (resumable; skips clips whose .json meta matches text+voice; regenerates changed lines;
         exits when nothing is left and STOP exists; log in audio.log)

## <lang>.json  ({lang, name, schema:1, count, talks:[...]})
talk  = {id, title, setting, category, tier(starter|beginner|elementary), learnerRole("A"|"B"),
         roles:{A,B}, voices:{A:"he"|"she", B:"he"|"she"}, lines:[line]}
line  = {idx, speaker("A"|"B"), role, learner(bool), text, meaning, reading, speak,
         audio:"smalltalk/audio/<lang>/<id>/<idx>.mp3", voice:"he"|"she", review?}
learner line adds:
         word (= text, for teacher {word}), prompt ("Say: …" / "Nói: …"),
         choices:[{text, reading, meaning, correct}] ×4 (1 correct + 3 distractors), answer (index of correct)
text/meaning/reading/speak are the same keys as data/curriculum.json talks, so a talk object drops into CURRICULUM[lang].talks.
meaning = English gloss (vi/zh/ja/es); Vietnamese gloss for en. reading = tone-marked pinyin (zh) / Hepburn romaji (ja), "" otherwise.
Distractors = learner replies from other topics in the same 50-topic block (same concept across all 5 langs; questions paired with questions).
Voices: voices.json "lesson" pack (he/she per lang); speakers alternate genders per topic (gender-agreeing pronouns/adjectives written per speaker).
Audio meta <idx>.json has edge-tts WordBoundary timings for lip sync.
