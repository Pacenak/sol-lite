# Adding a Platform

Implement the platform adapter contract in `src/sol_lite/platform/base.py`.

The adapter must detect actual installed shells and execute only the shell explicitly requested by the caller. Do not silently substitute another shell.

Add platform-specific tests for detection and command execution boundaries.
