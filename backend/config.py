from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # InsForge
    insforge_base_url: str = ""
    insforge_anon_key: str = ""
    insforge_service_key: str = ""

    # OpenRouter (provisioned via InsForge dashboard)
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-sonnet-4"

    # Kubernetes — uses in-cluster config, kubeconfig, or explicit path
    kubeconfig_path: str | None = None
    k8s_namespace: str = "default"

    # App
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
