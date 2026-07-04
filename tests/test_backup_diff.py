from netops.backup.collector import normalize
from netops.backup.differ import diff_configs


def test_normalize_strips_volatile_lines():
    raw = "\n".join(
        [
            "Building configuration...",
            "Current configuration : 1234 bytes",
            "! Last configuration change at 10:00 by admin",
            "hostname core-sw-01",
            "ntp clock-period 17179830",
            "ntp server 10.0.0.253",
        ]
    )
    result = normalize(raw)
    assert "hostname core-sw-01" in result
    assert "ntp server 10.0.0.253" in result
    assert "Building configuration" not in result
    assert "Current configuration" not in result
    assert "Last configuration change" not in result
    assert "clock-period" not in result


def test_diff_detects_change():
    old = "hostname a\ninterface Gi0/0\n"
    new = "hostname a\ninterface Gi0/0\n shutdown\n"
    changed, diff = diff_configs(old, new, "core-sw-01")
    assert changed is True
    assert "shutdown" in diff


def test_diff_reports_no_change_for_identical_config():
    config = "hostname a\nntp server 10.0.0.253\n"
    changed, diff = diff_configs(config, config, "core-sw-01")
    assert changed is False
    assert diff == ""
