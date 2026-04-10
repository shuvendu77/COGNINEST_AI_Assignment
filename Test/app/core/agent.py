from vanna import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.google.gemini import GeminiLlmService

from app.core.config import GOOGLE_API_KEY, get_db_path
from app.utils.sql_guard import ValidatedSqliteRunner


def _build_agent() -> tuple[Agent, DemoAgentMemory]:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is missing. Add it to your .env file.")

    llm_service = GeminiLlmService(api_key=GOOGLE_API_KEY, model="gemini-2.0-flash")
    runner = ValidatedSqliteRunner(get_db_path())
    memory = DemoAgentMemory()

    tool_registry = ToolRegistry()
    tool_registry.register_local_tool(RunSqlTool(runner), [])
    tool_registry.register_local_tool(VisualizeDataTool(), [])
    tool_registry.register_local_tool(SaveQuestionToolArgsTool(), [])
    tool_registry.register_local_tool(SearchSavedCorrectToolUsesTool(), [])

    class _DefaultUserResolver(UserResolver):
        async def resolve_user(self, request_context: RequestContext) -> User:
            return User(
                id="default_user",
                username="Default User",
                group_memberships=["admin"],
            )

    return Agent(
        llm_service=llm_service,
        tool_registry=tool_registry,
        user_resolver=_DefaultUserResolver(),
        agent_memory=memory,
    ), memory


# Module-level singletons — created once at import time
agent, agent_memory = _build_agent()
