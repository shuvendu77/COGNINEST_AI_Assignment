import re
import contextvars

from vanna.integrations.sqlite import SqliteRunner

# Per-request contextvar — set when SQL executes, read by the chat controller
last_executed_sql: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "last_executed_sql", default=None
)

_FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "EXEC", "XP_", "SP_", "GRANT", "REVOKE", "SHUTDOWN",
]


def validate_sql(sql: str) -> tuple[bool, str | None]:
    """Returns (is_valid, error_message). Permits SELECT queries only."""
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith("SELECT"):
        return False, "Only SELECT queries are allowed."
    for kw in _FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", sql_upper):
            return False, f"Forbidden keyword '{kw}' detected."
    if "SQLITE_MASTER" in sql_upper or "SQLITE_SEQUENCE" in sql_upper:
        return False, "Access to system tables is not allowed."
    return True, None


class ValidatedSqliteRunner(SqliteRunner):
    """SqliteRunner that validates SQL before execution and records it via contextvar."""

    async def run_sql(self, args, context):
        is_valid, error_msg = validate_sql(args.sql)
        if not is_valid:
            raise ValueError(f"SQL validation failed: {error_msg}")
        last_executed_sql.set(args.sql)
        return await super().run_sql(args, context)
