"""Static regression guard for sensitive logging arguments."""

import ast
from pathlib import Path

SENSITIVE_ATTRIBUTES = {
    "address",
    "aes_key",
    "buffer",
    "mac_uuid",
    "mobile_uuid",
    "package",
    "password",
    "sn",
    "token",
    "uid",
    "wurx_uuid",
}
SENSITIVE_NAMES = {
    "admin_pin",
    "aes_key",
    "ciphertext",
    "email",
    "encrypted_packet",
    "mac_uuid",
    "mobile_uuid",
    "packet",
    "password",
    "pin",
    "plaintext",
    "serial",
    "sn",
    "token",
    "uid",
    "wake_address",
    "wurx_uuid",
}
LOG_METHODS = {"debug", "info", "warning", "error", "exception"}


def test_logging_calls_do_not_reference_sensitive_values():
    """Sensitive attributes and byte dumps cannot re-enter logging calls."""

    root = Path("custom_components/ultraloq_ble")
    violations: list[str] = []
    for path in root.rglob("*.py"):
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(
                node.func, ast.Attribute
            ):
                continue
            if node.func.attr not in LOG_METHODS and node.func.attr != "debug":
                continue
            segment = ast.get_source_segment(source, node) or ""
            attributes = {
                child.attr
                for child in ast.walk(node)
                if isinstance(child, ast.Attribute)
            }
            names = {
                child.id for child in ast.walk(node) if isinstance(child, ast.Name)
            }
            if (
                attributes & SENSITIVE_ATTRIBUTES
                or names & SENSITIVE_NAMES
                or ".hex(" in segment
            ):
                violations.append(f"{path}:{node.lineno}: {segment}")

    assert violations == []


def test_connector_display_names_do_not_contain_addresses():
    """Connector retries use generic labels, not lock identifiers."""

    path = Path("custom_components/ultraloq_ble/utecio/ble/device.py")
    tree = ast.parse(path.read_text())
    connector_names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if (
            not isinstance(node.func, ast.Name)
            or node.func.id != "establish_connection"
        ):
            continue
        name_keyword = next(
            (keyword.value for keyword in node.keywords if keyword.arg == "name"),
            None,
        )
        assert isinstance(name_keyword, ast.Constant)
        assert isinstance(name_keyword.value, str)
        connector_names.append(name_keyword.value)

    assert sorted(connector_names) == sorted(
        [
            "Ultraloq lock",
            "Ultraloq lock",
            "Ultraloq wake receiver",
        ]
    )
