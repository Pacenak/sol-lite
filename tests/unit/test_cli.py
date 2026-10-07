from sol_lite.app import build_parser


def test_start_and_battle_commands_exist():
    assert build_parser().parse_args(["start"]).command == "start"
    args = build_parser().parse_args(["battle-test", "--live", "--agent", "sol_engineer"])
    assert args.live is True
    assert args.agent == "sol_engineer"
