from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v1"
    vector_store: str = "faiss"
    opensearch_url: str = "https://localhost:9200"
    opensearch_index: str = "fintech-policies"
    opensearch_user: str = "admin"
    opensearch_password: str = "admin"
    agent_verbose: bool = False
    log_level: str = "INFO"

settings = Settings()
