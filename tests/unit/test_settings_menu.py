from sol_lite.config.user_settings import UserSettingsStore, merge_searxng_settings
from sol_lite.ui.settings_menu import SettingsMenu


class ScriptedConsole:
    def __init__(self, answers):
        self.answers = list(answers)

    def input(self, prompt=""):
        if not self.answers:
            raise EOFError
        return self.answers.pop(0)

    def print(self, *args, **kwargs):
        return None


def test_search_menu_reads_and_writes_nested_searxng(tmp_path):
    store = UserSettingsStore(tmp_path / "settings.yaml")
    menu = SettingsMenu(
        store=store,
        repository_config={
            "searxng": {
                "searxng": {
                    "enabled": False,
                    "url": "http://10.10.40.10:30053/",
                    "timeout_seconds": 30,
                    "max_results": 8,
                    "categories": "general",
                    "language": "en",
                    "safesearch": 1,
                    "engines": "",
                }
            }
        },
        console=ScriptedConsole(["1", "y"]),
    )

    menu._search()

    saved = store.get("searxng")
    assert saved["searxng"]["enabled"] is True
    assert "enabled" not in saved or not isinstance(saved.get("enabled"), bool)


def test_settings_categories_dispatch(tmp_path):
    store = UserSettingsStore(tmp_path / "settings.yaml")
    menu = SettingsMenu(
        store=store,
        repository_config={},
        console=ScriptedConsole(["1", "2", "3", "4", "5", "6", "7", "8", "9", "r", "z", "b"]),
    )
    called = []
    menu._general = lambda: called.append("general")
    menu._agents = lambda: called.append("agents")
    menu._models = lambda: called.append("models")
    menu._runtime = lambda: called.append("runtime")
    menu._workspace_data = lambda: called.append("workspace")
    menu._search = lambda: called.append("search")
    menu._integrations = lambda: called.append("integrations")
    menu._display = lambda: called.append("display")
    menu._view = lambda: called.append("view")
    menu._reset = lambda: called.append("reset")

    assert menu.run() is True
    assert called == [
        "general",
        "agents",
        "models",
        "runtime",
        "workspace",
        "search",
        "integrations",
        "display",
        "view",
        "reset",
    ]


def test_merge_searxng_settings_applies_flat_and_nested_overrides():
    repository = {
        "searxng": {
            "enabled": False,
            "url": "http://example",
            "timeout_seconds": 15,
        }
    }

    flat = merge_searxng_settings(repository, {"enabled": True})
    nested = merge_searxng_settings(
        repository,
        {"searxng": {"url": "http://search.example"}},
    )

    assert flat == {
        "searxng": {
            "enabled": True,
            "url": "http://example",
            "timeout_seconds": 15,
        }
    }
    assert nested["searxng"]["url"] == "http://search.example"
    assert nested["searxng"]["enabled"] is False
    assert "enabled" not in flat
