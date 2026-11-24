from app.security.validator import validate_select_sql


def test_safe_select_is_valid():
    result = validate_select_sql("SELECT TOP 10 airport_code, airport_name FROM dbo.Airport ORDER BY airport_name")
    assert result.is_valid is True
    assert "TOP 10" in result.normalized_sql.upper()


def test_drop_statement_rejected():
    result = validate_select_sql("DROP TABLE dbo.Airline")
    assert result.is_valid is False


def test_comment_and_injection_rejected():
    result = validate_select_sql("SELECT * FROM dbo.Airport -- comment; DROP TABLE dbo.Airline")
    assert result.is_valid is False
