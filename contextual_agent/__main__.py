import logging
import click
from .config import DEFAULT_CONTEXTUAL_AGENT_URL

# Attempt to import A2A/ADK dependencies
try:
    import uvicorn
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import AgentCapabilities, AgentCard, AgentSkill
    from .agent import root_agent
    from .agent_executor import ContextualAgentExecutor
    ADK_AVAILABLE = True
except ImportError as e:
    ADK_AVAILABLE = False
    missing_dep = e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--host",
    default=DEFAULT_CONTEXTUAL_AGENT_URL.split(":")[1].replace("//", ""),
    help="Host to bind the server to.",
)
@click.option(
    "--port",
    default=int(DEFAULT_CONTEXTUAL_AGENT_URL.split(":")[2]),
    help="Port to bind the server to.",
)
def main(host: str, port: int):
    """Runs the CONTEXTUAL AGENT ADK agent as an A2A server."""
    # Fallback to simple HTTP if ADK/A2A deps missing
    if not ADK_AVAILABLE:
        logger.warning(f"! ! ! CONTEXTUAL AGENT ADK or A2A SDK dependencies not found ({missing_dep}), falling back to simple HTTP service.")
        return
    logger.info(f"Configuring CONTEXTUAL AGENT A2A server...")
    
    try:
        agent_card = AgentCard(
            name=root_agent.name,
            description=root_agent.description,
            url=f"http://{host}:{port}",
            version="1.0.0",
            capabilities=AgentCapabilities(
                streaming=False,
                pushNotifications=False,
            ),
            defaultInputModes=['text'],
            defaultOutputModes=['text'],
            skills=[
                AgentSkill(
                    id='client_profiling',
                    name='Build Ideal Client Profile',
                    description='Interactive conversation to help build a detailed ideal client profile for sales and lead generation.',
                    examples=[
                        "Help me build my ideal client profile",
                        "I need to understand my target customers better",
                        "What questions should I ask to identify my perfect client?",
                    ],
                    tags=['sales', 'lead-generation', 'client-profiling', 'conversation'],
                ),
                AgentSkill(
                    id='profile_management',
                    name='Manage Client Profile Data',
                    description='Update and present client profile information gathered through conversation.',
                    examples=[
                        "Show me my current client profile",
                        "Update my target industry information",
                        "What client profile data do we have so far?",
                    ],
                    tags=['data-management', 'profile', 'update'],
                )
            ],
        )
    except AttributeError as e:
        logger.error(
            f"Error accessing attributes from contextual_agent: {e}. Is agent.py correct?"
        )
        raise

    try:
        agent_executor = ContextualAgentExecutor()
        
        task_store = InMemoryTaskStore()
        
        request_handler = DefaultRequestHandler(agent_executor, task_store)
        
        app_builder = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler
        )
        
        # Add custom endpoint for client profile updates
        from starlette.applications import Starlette
        from starlette.responses import JSONResponse
        from starlette.routing import Route
        import json as json_lib
        
        # Global storage for the latest client profile
        latest_client_profile = {"profile": None, "timestamp": None}
        
        async def receive_client_profile(request):
            """Endpoint to receive client profile updates"""
            try:
                body = await request.body()
                profile_data = json_lib.loads(body)
                
                # Store the profile with timestamp
                import datetime
                latest_client_profile["profile"] = profile_data
                latest_client_profile["timestamp"] = datetime.datetime.now().isoformat()
                
                logger.info(f"Received client profile update: {len(str(profile_data))} characters")
                
                return JSONResponse({
                    "status": "success",
                    "message": "Client profile received and stored",
                    "timestamp": latest_client_profile["timestamp"]
                })
            except Exception as e:
                logger.error(f"Error receiving client profile: {e}")
                return JSONResponse({
                    "status": "error",
                    "message": str(e)
                }, status_code=400)
        
        async def get_client_profile(request):
            """Endpoint to retrieve the latest client profile"""
            if latest_client_profile["profile"] is None:
                return JSONResponse({
                    "status": "no_profile",
                    "message": "No client profile available yet"
                }, status_code=404)
            
            return JSONResponse({
                "status": "success",
                "profile": latest_client_profile["profile"],
                "timestamp": latest_client_profile["timestamp"]
            })
        
        # Get the Starlette app and add custom routes
        starlette_app = app_builder.build()
        
        # Add the custom routes
        profile_routes = [
            Route("/client-profile", receive_client_profile, methods=["POST"]),
            Route("/client-profile", get_client_profile, methods=["GET"]),
        ]
        
        # Extend the existing routes
        starlette_app.router.routes.extend(profile_routes)
        
        logger.info(f"Starting CONTEXTUAL AGENT A2A server on {host}:{port}")
        logger.info(f"Client profile endpoints available at:")
        logger.info(f"  POST http://{host}:{port}/client-profile - Receive profile updates")
        logger.info(f"  GET  http://{host}:{port}/client-profile - Retrieve latest profile")
        
        # Start the Server
        import uvicorn
    
        logger.info(f"Starting Contextual Agent A2A server on http://{host}:{port}/")
        uvicorn.run(starlette_app, host=host, port=port)
            
    except Exception as e:
        logger.error(f"Failed to start CONTEXTUAL AGENT A2A server: {e}")
        raise


if __name__ == '__main__':
    main()
