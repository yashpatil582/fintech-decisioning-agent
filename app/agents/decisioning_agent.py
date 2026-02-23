"""DecisioningAgent: LangChain tool-calling agent on AWS Bedrock."""
from __future__ import annotations
import json, logging
from typing import Any
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.agents.tools import build_tools
from app.models.schemas import DecisionRequest, DecisionResponse
from app.rag.retriever import build_retriever
from app.utils.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert financial decisioning agent.
Evaluate loan/credit applications using company policies and risk guidelines.
ALWAYS use policy_retriever before deciding. Use credit_scorer, dti_calculator, and fraud_check as needed.
Respond ONLY with valid JSON:
{"decision":"APPROVE"|"DECLINE"|"REFER","confidence":<0-1>,"reasoning":"...","risk_factors":["..."],"retrieved_policies":["..."]}"""

class DecisioningAgent:
    def __init__(self):
        from langchain_aws import ChatBedrock
        self.llm = ChatBedrock(model_id=settings.bedrock_model_id, region_name=settings.aws_region,
                               model_kwargs={"temperature": 0.1, "max_tokens": 2048})
        self.retriever = build_retriever()
        self.tools = build_tools(self.retriever)
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.executor = AgentExecutor(agent=agent, tools=self.tools, verbose=settings.agent_verbose,
                                      max_iterations=5, handle_parsing_errors=True)
        logger.info("DecisioningAgent ready | model=%s | tools=%s", settings.bedrock_model_id, [t.name for t in self.tools])

    async def run(self, request: DecisionRequest) -> DecisionResponse:
        agent_input = (f"Decision type: {request.decision_type.value}\n"
                       f"Applicant: {json.dumps(request.applicant.model_dump(exclude_none=True), indent=2)}\n"
                       f"Question: {request.query}")
        result = await self.executor.ainvoke({"input": agent_input})
        raw = result.get("output", "{}")
        try:
            parsed: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"decision": "REFER", "confidence": 0.5, "reasoning": raw, "risk_factors": [], "retrieved_policies": []}
        return DecisionResponse(session_id=request.session_id, raw_agent_output=raw, **parsed)
