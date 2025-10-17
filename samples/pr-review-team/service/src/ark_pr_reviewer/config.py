from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    service_name: str = "ark-pr-reviewer"
    log_level: str = "INFO"
    
    github_token: str
    github_api_url: str = "https://api.github.com"
    
    jira_base_url: str
    jira_username: str | None = None
    jira_api_token: str | None = None
    jira_timeout: int = 10
    jira_fallback_enabled: bool = True
    
    aws_region: str = "us-east-1"
    s3_bucket: str
    s3_prefix: str = "reviews"
    
    kubernetes_namespace: str = "ark-pr-review"
    team_name: str = "pr-review-team"
    
    review_timeout: int = 300
    
    metrics_port: int = 8000
    api_port: int = 8080


settings = Settings()

