from sol_lite.prompts import PromptLoader


def test_variables(tmp_path):
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "00_test.md").write_text(
        "{{WORKSPACE}} {{PROMPT_DIRECTORY}} {{FAULT_LOG}} {{DATE}} {{DATETIME}}",
        encoding="utf-8",
    )
    loader = PromptLoader(prompts, tmp_path / "workspace", tmp_path / "faults.json")
    text = loader.load("00_test.md")
    assert "{{WORKSPACE}}" not in text
    assert "{{DATE}}" not in text
