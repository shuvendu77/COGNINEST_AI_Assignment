from fastapi import APIRouter, HTTPException
from vanna.core.user import RequestContext
from vanna.core.rich_component import ComponentType
from vanna import DataFrameComponent
from vanna.components.rich.data.chart import ChartComponent

from app.core.agent import agent
from app.models.schemas import ChatRequest
from app.utils.sanitize import sanitize_value
from app.utils.sql_guard import last_executed_sql

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):
    context = RequestContext()
    try:
        columns, rows, row_count = [], [], 0
        chart_data, chart_type = None, None
        message_parts: list[str] = []
        agent_error: str | None = None

        async for component in agent.send_message(context, request.question):
            rc = component.rich_component
            sc = component.simple_component

            if rc.type == ComponentType.DATAFRAME:
                columns = rc.columns
                rows = [[sanitize_value(v) for v in row.values()] for row in rc.rows]
                row_count = rc.row_count

            elif rc.type == ComponentType.CHART:
                chart_data = rc.data
                chart_type = rc.chart_type

            elif rc.type == ComponentType.TEXT:
                if hasattr(rc, "content") and rc.content:
                    message_parts.append(rc.content)

            elif rc.type == ComponentType.STATUS_CARD:
                if (
                    getattr(rc, "status", "") == "error"
                    and getattr(rc, "title", "") == "Error Processing Message"
                ):
                    agent_error = (getattr(sc, "text", "") if sc else "") or "Agent reported an internal error."

        if agent_error:
            raise HTTPException(status_code=429, detail=agent_error)

        return {
            "message": " ".join(message_parts).strip() or "Query executed successfully.",
            "sql_query": last_executed_sql.get(),
            "columns": columns,
            "rows": rows,
            "row_count": row_count,
            "chart": chart_data,
            "chart_type": chart_type,
        }

    except HTTPException:
        raise
    except Exception as e:
        err = str(e)
        raise HTTPException(
            status_code=429 if "429" in err or "RESOURCE_EXHAUSTED" in err else 500,
            detail=err,
        )
