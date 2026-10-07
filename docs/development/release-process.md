# Release Process

1. Update version.
2. Update changelog.
3. Run compileall.
4. Run pytest.
5. Run Ruff.
6. Run battle tests.
7. Run live smoke validation when Ollama is available.
8. Regenerate `BUILD_MANIFEST.json`.
9. Inspect ZIP contents for source, docs, launchers, installers, tests and skills.
10. Verify the normal-start path does not invoke dependency installation.
