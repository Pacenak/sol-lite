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
    assert parser.parse_args(["connect", "--command-url", "https://command.example"]).invite_code is None
    assert parser.parse_args(["command-status"]).command == "command-status"
    assert parser.parse_args(["sync-skills"]).command == "sync-skills"
    assert parser.parse_args(["disconnect"]).command == "disconnect"
    assert parser.parse_args(["google-status"]).command == "google-status"
    assert parser.parse_args(["jira-status"]).command == "jira-status"
    assert parser.parse_args(["voice-status"]).command == "voice-status"
    jira = parser.parse_args(["jira-disconnect", "--name", "work"])
    assert jira.name == "work"


def test_connect_prompts_and_prints_progress(monkeypatch, capsys):
    from sol_lite.app import main
    monkeypatch.setattr("sys.argv", ["sol-lite", "connect", "--command-url", "https://command.example"])
    monkeypatch.setattr("getpass.getpass", lambda prompt: "secret-invite")
    def pair(url, invite, *, name, progress):
        assert invite == "secret-invite"
        progress("Registered. Waiting for approval.")
        return {"instance_id": "test-id", "sectors": ["home"]}
    monkeypatch.setattr("sol_lite.integrations.sol_command.SolCommandClient.pair", pair)
    main()
    output = capsys.readouterr().out
    assert "Waiting for approval" in output
    assert "Paired with SOL-Command" in output
    assert "secret-invite" not in output
