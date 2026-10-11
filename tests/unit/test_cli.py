from sol_lite.app import build_parser


def test_start_and_battle_commands_exist():
    assert build_parser().parse_args(["start"]).command == "start"
    args = build_parser().parse_args(["battle-test", "--live", "--agent", "sol_engineer"])
    assert args.live is True
    assert args.agent == "sol_engineer"


def test_command_and_google_cli_commands_exist():
    parser = build_parser()
    connect = parser.parse_args([
        "connect", "--command-url", "https://command.example", "--invite-code", "invite",
    ])
    assert connect.command == "connect"
    assert connect.command_url == "https://command.example"
    assert parser.parse_args(["command-status"]).command == "command-status"
    assert parser.parse_args(["sync-skills"]).command == "sync-skills"
    assert parser.parse_args(["disconnect"]).command == "disconnect"
    assert parser.parse_args(["google-status"]).command == "google-status"
    assert parser.parse_args(["jira-status"]).command == "jira-status"
    assert parser.parse_args(["voice-status"]).command == "voice-status"
    jira = parser.parse_args(["jira-disconnect", "--name", "work"])
    assert jira.name == "work"
