import json
import logging
from typing import Any
from datetime import datetime
from pathlib import Path

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import DataPart, Part, TaskState

from google.adk import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types as genai_types

from .agent import root_agent
from .config import DEFAULT_UI_CLIENT_URL

logger = logging.getLogger(__name__)

# Initialize logging to file
root_path = Path.cwd()
log_file = root_path / "contextual_agent/contextual_agent.log"

def log_to_file(message: str):
    """Write log message to file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write('\n')
        f.write(f"[{timestamp}] {message}\n")
        f.write('\n')

# Clear previous logs and start fresh for this call
with open(log_file, 'w', encoding='utf-8') as f:
    f.write(f"=== CONTEXTUAL AGENT LOG - {datetime.now().isoformat()} ===\n\n")

class ContextualAgentExecutor(AgentExecutor):
    """Executes the Contextual ADK agent logic in response to A2A requests."""

    def __init__(self):
        self._adk_agent = root_agent
        self._adk_runner = Runner(
            app_name="contextual_agent_runner",
            agent=self._adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
        )
        logger.info("ContextualAgentExecutor initialized with ADK Runner.")

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        
        logger.info(f"DEBUG: Context message parts: {[str(part) for part in context.message.parts]}")

        if not context.current_task:
            task_updater.submit(message=context.message)

        task_updater.start_work(
            message=task_updater.new_agent_message(
                parts=[
                    Part(root=DataPart(data={"status": "Starting client profile conversation..."}))
                ]
            )
        )

        # Extract user message from context
        user_message: str = "Hello, I need help building my ideal client profile."
        ui_client_url = DEFAULT_UI_CLIENT_URL

        if context.message and context.message.parts:
            for part_union in context.message.parts:
                part = part_union.root
                if isinstance(part, DataPart):
                    # Try to extract user message or query
                    if "message" in part.data:
                        user_message = part.data["message"]
                    elif "query" in part.data:
                        user_message = part.data["query"]
                    elif "text" in part.data:
                        user_message = part.data["text"]
                    
                    if "ui_client_url" in part.data:
                        ui_client_url = part.data["ui_client_url"]

        # Prepare input for ADK Agent
        agent_input_dict = {
            "message": user_message,
            "ui_client_url": ui_client_url,
            "operation": "build_client_profile"
        }
        
        # Create ADK content
        adk_content = genai_types.Content(
            parts=[
                genai_types.Part(text=user_message),
                genai_types.Part(text=json.dumps(agent_input_dict))
            ]
        )

        # Session handling
        session_id_for_adk = context.context_id
        logger.info(f"Task {context.task_id}: Using ADK session_id: '{session_id_for_adk}'")

        session: Session | None = None
        if session_id_for_adk:
            try:
                session = await self._adk_runner.session_service.get_session(
                    app_name=self._adk_runner.app_name,
                    user_id="a2a_user",
                    session_id=session_id_for_adk,
                )
            except Exception as e:
                logger.exception(f"Task {context.task_id}: Exception during get_session: {e}")
                session = None

            if not session:
                logger.info(f"Task {context.task_id}: Creating new ADK session")
                try:
                    session = await self._adk_runner.session_service.create_session(
                        app_name=self._adk_runner.app_name,
                        user_id="a2a_user",
                        session_id=session_id_for_adk,
                        state={"conversation_started": True},
                    )
                    if session:
                        logger.info(f"Task {context.task_id}: Successfully created ADK session")
                except Exception as e:
                    logger.exception(f"Task {context.task_id}: Exception during create_session: {e}")
                    session = None

        if not session:
            error_message = "Failed to establish ADK session"
            logger.error(f"Task {context.task_id}: {error_message}")
            task_updater.failed(
                message=task_updater.new_agent_message(
                    parts=[
                        Part(
                            root=DataPart(
                                data={"error": f"Internal error: {error_message}"}
                            )
                        )
                    ]
                )
            )
            return

        # Execute the ADK Agent
        try:
            logger.info(f"Task {context.task_id}: Calling ADK run_async")
            final_result = {"status": "completed", "conversation": "active"}
            
            async for event in self._adk_runner.run_async(
                user_id="a2a_user",
                session_id=session_id_for_adk,
                new_message=adk_content,
            ):
                log_entry = f" ** - - - - - ** \n [Event] Author: {event.author}, \n Type: {type(event).__name__}, \n Final: {event.is_final_response()}, \n Content: {event.content}"
                log_to_file(log_entry)
                
                if event.is_final_response():
                    if event.content and event.content.parts:
                        # Extract the agent's response
                        for part in event.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                # Handle function calls if any
                                if part.function_call.name in ["update_client_profile", "present_client_profile"]:
                                    final_result["function_called"] = part.function_call.name
                                    if part.function_call.args:
                                        final_result["function_args"] = part.function_call.args
                            elif hasattr(part, "text") and part.text:
                                final_result["response"] = part.text

            task_updater.add_artifact(
                parts=[Part(root=DataPart(data=final_result))],
                name="client_profile_conversation",
            )
            task_updater.complete()

        except Exception as e:
            logger.exception(f"Task {context.task_id}: Error running Contextual ADK agent: {e}")
            task_updater.failed(
                message=task_updater.new_agent_message(
                    parts=[Part(root=DataPart(data={"error": f"ADK Agent error: {e}"}))]
                )
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        logger.warning(f"Cancellation not implemented for Contextual Agent task: {context.task_id}")
        task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        task_updater.failed(
            message=task_updater.new_agent_message(
                parts=[Part(root=DataPart(data={"error": "Task cancelled"}))]
            )
        )
