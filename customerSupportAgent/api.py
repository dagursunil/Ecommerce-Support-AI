from contextlib import asynccontextmanager
from dataclasses import dataclass
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents import SQLiteSession
from agents.memory import OpenAIResponsesCompactionSession

from customerSupportAgent.context import SupportContext
from customerSupportAgent.service import CustomerSupportAgentService


service = CustomerSupportAgentService()


@dataclass
class CustomerSession:
    app_context: SupportContext
    underlying_session: SQLiteSession
    session: OpenAIResponsesCompactionSession


# For now, keep active application sessions in memory.
active_sessions: dict[str, CustomerSession] = {}


class CreateSessionRequest(BaseModel):
    customer_id: int


class CreateSessionResponse(BaseModel):
    session_id: str


class MessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    response: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    await service.start()

    try:
        yield
    finally:
        await service.stop()


app = FastAPI(
    title="eComm Support AI",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post(
    "/sessions",
    response_model=CreateSessionResponse,
)
async def create_session(
    request: CreateSessionRequest,
):
    session_id = str(uuid4())

    underlying_session = SQLiteSession(
        session_id
    )

    session = OpenAIResponsesCompactionSession(
        session_id=session_id,
        underlying_session=underlying_session,
    )

    app_context = SupportContext(
        customer_id=request.customer_id,
    )

    active_sessions[session_id] = CustomerSession(
        app_context=app_context,
        underlying_session=underlying_session,
        session=session,
    )

    return CreateSessionResponse(
        session_id=session_id,
    )


@app.post(
    "/sessions/{session_id}/messages",
    response_model=MessageResponse,
)
async def send_message(
    session_id: str,
    request: MessageRequest,
):
    customer_session = active_sessions.get(
        session_id
    )

    if customer_session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        )

    app_context = customer_session.app_context

    agent_input = f"""
Authenticated customer context:
customer_id={app_context.customer_id}

Customer message:
{request.message}
""".strip()

    result = await service.run(
        message=agent_input,
        app_context=app_context,
        session=customer_session.session,
    )

    return MessageResponse(
        response=result.final_output,
    )