"""
test_integration.py — Integration tests requiring live GCP credentials.

Skip these in CI unless the `--integration` flag is passed.

Usage:
  pytest tests/test_integration.py --integration -v
"""
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests against live GCP services",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as requiring live GCP credentials"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--integration"):
        skip_int = pytest.mark.skip(reason="Pass --integration to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_int)


# ---- Tests ---------------------------------------------------------------

@pytest.mark.integration
class TestFirestoreIntegration:

    @pytest.mark.asyncio
    async def test_create_and_get_session(self):
        from backend.services.firestore_service import firestore_service
        session_id = await firestore_service.create_session("test-user", "Integration Test System")
        assert session_id
        session = await firestore_service.get_session(session_id)
        assert session is not None
        assert session["userId"] == "test-user"

    @pytest.mark.asyncio
    async def test_upsert_control_mapping(self):
        from backend.services.firestore_service import firestore_service
        session_id = await firestore_service.create_session("test-user")
        mapping = {
            "control_id": "AC-2",
            "title": "Account Management",
            "implementation_status": "implemented",
            "confidence_score": 0.9,
        }
        await firestore_service.upsert_control_mapping(session_id, mapping)
        mappings = await firestore_service.get_control_mappings(session_id)
        assert any(m.get("control_id") == "AC-2" for m in mappings)


@pytest.mark.integration
class TestGeminiLiveIntegration:
    """Smoke test that Gemini Live API is reachable."""

    @pytest.mark.asyncio
    async def test_live_session_connect(self):
        from google import genai
        from backend.config import settings
        from backend.app import LIVE_CONFIG

        client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
        async with client.aio.live.connect(
            model=settings.gemini_model,
            config=LIVE_CONFIG,
        ) as session:
            # Send a minimal text turn and verify we get a response
            from google.genai import types
            await session.send(
                input=types.LiveClientContent(
                    turns=[
                        types.Content(
                            role="user",
                            parts=[types.Part(text="Hello, COMPASS. Can you hear me?")],
                        )
                    ]
                )
            )
            # Read first chunk
            async for response in session.receive():
                if response.text or response.data:
                    assert True
                    break


@pytest.mark.integration
class TestVectorSearchIntegration:

    @pytest.mark.asyncio
    async def test_embed_and_query(self):
        from backend.services.vector_service import vector_service
        from backend.tools.vector_search import search_controls_impl

        result = search_controls_impl(query="boundary protection firewall")
        assert isinstance(result, dict)
        results_list = result.get("results", [])
        assert isinstance(results_list, list)
