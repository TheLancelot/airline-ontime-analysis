import subprocess
import sys
from pathlib import Path

from app.auth.service import AuthService
from app.auth.storage import UserStore
from scripts import create_admin


def build_auth_service(tmp_path: Path) -> AuthService:
    return AuthService(UserStore(tmp_path / "users.json"))


def test_admin_script_can_create_account_with_hidden_password_prompt(tmp_path, monkeypatch, capsys):
    service = build_auth_service(tmp_path)
    answers = iter(["Password123", "Password123"])
    monkeypatch.setattr(create_admin.getpass, "getpass", lambda prompt: next(answers))

    exit_code = create_admin.main(["new_admin"], service=service)

    assert exit_code == 0
    assert service.store.get_user("new_admin").role == "admin"
    assert "Admin account created" in capsys.readouterr().out


def test_admin_script_promotes_existing_user_after_password_check(tmp_path, monkeypatch):
    service = build_auth_service(tmp_path)
    service.register_user("existing_user", "Password123")
    monkeypatch.setattr(create_admin.getpass, "getpass", lambda prompt: "Password123")

    exit_code = create_admin.main(["existing_user"], service=service)

    assert exit_code == 0
    assert service.store.get_user("existing_user").role == "admin"


def test_admin_script_does_not_promote_with_incorrect_password(tmp_path, monkeypatch):
    service = build_auth_service(tmp_path)
    service.register_user("existing_user", "Password123")
    monkeypatch.setattr(create_admin.getpass, "getpass", lambda prompt: "Incorrect123")

    exit_code = create_admin.main(["existing_user"], service=service)

    assert exit_code == 1
    assert service.store.get_user("existing_user").role == "user"


def test_admin_script_can_be_invoked_from_another_working_directory(tmp_path):
    project_dir = Path(create_admin.__file__).resolve().parents[1]
    script_path = project_dir / "scripts" / "create_admin.py"

    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Create an admin account" in result.stdout
