"""
AWS Bedrock LLM client via LangChain.
Uses Claude 3 Sonnet by default; configurable via env.
"""

import os
import boto3
import logging
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

BEDROCK_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")


def get_bedrock_client() -> ChatBedrock:
    """Return a LangChain ChatBedrock instance."""
    session = boto3.Session(region_name=BEDROCK_REGION)
    bedrock_runtime = session.client("bedrock-runtime")

    llm = ChatBedrock(
        client=bedrock_runtime,
        model_id=BEDROCK_MODEL_ID,
        model_kwargs={
            "temperature": 0.0,   # deterministic for credit decisions
            "max_tokens": 2048,
        },
    )
    logger.info("Bedrock client initialised: model=%s region=%s", BEDROCK_MODEL_ID, BEDROCK_REGION)
    return llm


def ping_bedrock() -> bool:
    """Return True if Bedrock is reachable."""
    try:
        llm = get_bedrock_client()
        llm.invoke([HumanMessage(content="ping")])
        return True
    except Exception as exc:
        logger.warning("Bedrock ping failed: %s", exc)
        return False
