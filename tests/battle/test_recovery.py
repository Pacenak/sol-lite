from sol_lite.faults.log import FaultLog


def test_corrupt_fault_log_recovers(tmp_path):
    path = tmp_path / "faults.json"
    path.write_text("{bad json", encoding="utf-8")
    log = FaultLog(path)
    assert log.log(category="recovery", code="CORRUPTED_LOG")["code"] == "CORRUPTED_LOG"
