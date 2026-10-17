# Voice and listening

Use `/voice status` to see your selected engines and switches. `/voice on` enables listening and spoken replies when both engines are available; `/voice off` disables both. Settings persist across restarts.

- `/listen`: record one message, print the transcript, and send it to the active agent.
- `/listen off` / `/listen on`: disable or enable microphone recording. Enabling does not start recording.
- `/speak on` / `/speak off`: explicitly enable or disable spoken replies. Bare `/speak` toggles.
- `/voice model small`: use the multilingual Whisper small model (new-install default). Existing model choices are preserved; `base` is faster on slower CPUs.
- `/voice language en`: pin recognition to English; `/voice language auto` restores detection.
- `/voice tts local`: select Kokoro for natural local speech. It requires the voice extra, compatible Python, eSpeak-NG, and model weights.
- `/voice tts platform`: use the operating system speech engine.
- `/voice voice af_bella`: set the Kokoro voice; `/voice speed 1.1` adjusts neural speech speed.
- `/voice agent sol_pa af_bella`: override the voice for an agent. Choose voice IDs supported by the selected provider.

Whisper recognizes speech; Kokoro or a configured speech endpoint produces spoken replies. The microphone is active only during `/listen`. Recording stops after silence, Enter, or 20 seconds; Ctrl+C cancels. Short audio before speech onset is retained to avoid cutting the first word. Review the printed transcript when accuracy matters. Recognition quality depends on microphone, background noise, language, and model.

Hosted engines can be selected with `/voice stt endpoint:NAME` or `/voice tts endpoint:NAME`. Configure NAME under `endpoints` in `data/state/voice.json`, using `base_url`, optional `api_key_env`, and provider model/voice fields `stt_model`, `tts_model`, `tts_voice`. Credentials belong in the named environment variable. Hosted providers receive audio or reply text when selected. TTS requests WAV for playback. No hosted service is selected automatically.

Run `sol-lite voice-status` for local package/model diagnostics. First use may download weights. A readiness report does not verify microphone permissions or speaker output. Test a harmless spoken sentence and response on your device. Platform speech uses the system default voice and speed.
