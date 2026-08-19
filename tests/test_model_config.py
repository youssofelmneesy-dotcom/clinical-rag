from backend.generation.providers import ModelConfig


def test_model_config_loads_roles_from_environment(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "openrouter")
    monkeypatch.setenv("QUERY_MODEL", "query-model")
    monkeypatch.setenv("GENERATION_MODEL", "generation-model")
    monkeypatch.setenv("VERIFIER_MODEL", "verifier-model")
    monkeypatch.setenv("RERANKER_MODEL", "reranker-model")
    config = ModelConfig.from_env()
    assert config.model_provider == "openrouter"
    assert config.query_model == "query-model"
    assert config.generation_model == "generation-model"
    assert config.verifier_model == "verifier-model"
    assert config.reranker_model == "reranker-model"
