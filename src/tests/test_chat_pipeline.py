from app.services.gemini_client import GeminiClient


from types import SimpleNamespace

import pytest

from app.config import settings
from app.services.gemini_client import GeminiClient, GeminiServiceError


class FakeModels:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.model = None
        self.contents = None

    def generate_content(self, *, model, contents):
        self.model = model
        self.contents = contents
        if self.error:
            raise self.error
        return self.response


class FakeGenAIClient:
    def __init__(self, models):
        self.models = models


def test_fallback_chat_response_is_safe():
    response = GeminiClient(api_key="").generate_sql("Show me the first 10 airports")
    assert response["refusal_reason"] is None
    assert "SELECT" in response["sql"].upper()
    assert "DBO.AIRPORT" in response["sql"].upper()


def test_fallback_recognizes_carrier_count():
    response = GeminiClient(api_key="").generate_sql("how many total carriers in the database")
    assert response["refusal_reason"] is None
    assert "COUNT(DISTINCT CARRIER_CODE)" in response["sql"].upper()
    assert "DBO.AIRLINE" in response["sql"].upper()


def test_current_google_genai_client_uses_configured_model_and_parses_json():
    models = FakeModels(
        response=SimpleNamespace(
            text='{"sql":"SELECT COUNT(*) AS total FROM dbo.Airline","refusal_reason":null,"explanation":"Counts airlines."}'
        )
    )
    client = GeminiClient(api_key="test-key", client=FakeGenAIClient(models))

    response = client.generate_sql("How many airlines are there?")

    assert models.model == settings.GEMINI_MODEL
    assert "How many airlines are there?" in models.contents
    assert response["sql"] == "SELECT COUNT(*) AS total FROM dbo.Airline"
    assert response["refusal_reason"] is None


def test_gemini_errors_are_not_silently_replaced_with_fallback_sql():
    client = GeminiClient(
        api_key="test-key",
        client=FakeGenAIClient(FakeModels(error=RuntimeError("provider unavailable"))),
    )

    with pytest.raises(GeminiServiceError, match="could not generate"):
        client.generate_sql("How many airlines are there?")
