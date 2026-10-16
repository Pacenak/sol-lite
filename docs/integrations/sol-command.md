# SOL-Command connection

SOL-Lite does not need SOL-Command. The full standalone setup, daily use, and optional pairing steps are in the [SOL-Lite integration guide](sol-lite.md).

**Beginner runbook (interns, engineers, admins):** [Link SOL-Lite to SOL-Command](../user/dummies-command-link.md). That chapter is BookStack-ready; each `##` section can become its own page later.

Pairing is optional. `sol-lite connect` stores the instance credential in the OS keyring after a Command administrator approves the pending SOL-Lite instance. `sol-lite command-status` is the live check. `sol-lite sync-skills` downloads assigned-sector skills into pending review and does not activate them. Jarvis proposals stay off until a Command administrator grants `lite-access`. `sol-lite disconnect` removes the local credential; an administrator also has to delete the instance on Command.
