from app.auth.service import AuthService
from app.auth.storage import UserStore


def test_register_and_authenticate(tmp_path):
    store = UserStore(tmp_path / "users.json")
    service = AuthService(store)

    user = service.register_user("demo_user", "Password123")
    assert user.username == "demo_user"
    assert service.authenticate_user("demo_user", "Password123").username == "demo_user"
    assert service.authenticate_user("demo_user", "WrongPassword") is None


def test_password_policy_rejection(tmp_path):
    store = UserStore(tmp_path / "users.json")
    service = AuthService(store)

    try:
        service.register_user("demo", "short")
        raise AssertionError("Expected ValueError for weak password")
    except ValueError:
        pass
