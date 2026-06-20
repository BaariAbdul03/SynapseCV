import logging

from sqlalchemy import inspect, text

from app.extensions import db

logger = logging.getLogger(__name__)


def ensure_database_compatibility() -> None:
    """
    Apply tiny, idempotent schema fixes for deployments that used db.create_all()
    before newer models were added. This is not a replacement for Alembic, but it
    keeps existing Render/Supabase databases from failing on missing columns.
    """
    engine = db.engine
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    def table_columns(table_name: str) -> set[str]:
        if table_name not in tables:
            return set()
        return {column["name"] for column in inspector.get_columns(table_name)}

    ddl_statements: list[str] = []

    user_columns = table_columns("users")
    if user_columns:
        if "name" not in user_columns:
            ddl_statements.append("ALTER TABLE users ADD COLUMN name VARCHAR(100)")
        if "password_hash" not in user_columns:
            ddl_statements.append("ALTER TABLE users ADD COLUMN password_hash VARCHAR(256)")
        if "oauth_provider" not in user_columns:
            ddl_statements.append("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(50)")
        if "oauth_id" not in user_columns:
            ddl_statements.append("ALTER TABLE users ADD COLUMN oauth_id VARCHAR(100)")
        if "created_at" not in user_columns:
            ddl_statements.append("ALTER TABLE users ADD COLUMN created_at TIMESTAMP")

    analysis_columns = table_columns("analyses")
    if analysis_columns:
        if "target_role" not in analysis_columns:
            ddl_statements.append("ALTER TABLE analyses ADD COLUMN target_role VARCHAR(150)")
        if "github_url" not in analysis_columns:
            ddl_statements.append("ALTER TABLE analyses ADD COLUMN github_url VARCHAR(255)")
        if "linkedin_url" not in analysis_columns:
            ddl_statements.append("ALTER TABLE analyses ADD COLUMN linkedin_url VARCHAR(255)")

    api_key_columns = table_columns("api_keys")
    if api_key_columns:
        if "name" not in api_key_columns:
            ddl_statements.append("ALTER TABLE api_keys ADD COLUMN name VARCHAR(100)")
        if "key_prefix" not in api_key_columns:
            ddl_statements.append("ALTER TABLE api_keys ADD COLUMN key_prefix VARCHAR(32)")
        if "key_hash" not in api_key_columns:
            ddl_statements.append("ALTER TABLE api_keys ADD COLUMN key_hash VARCHAR(64)")
        if "created_at" not in api_key_columns:
            ddl_statements.append("ALTER TABLE api_keys ADD COLUMN created_at TIMESTAMP")

    if engine.dialect.name == "postgresql" and "api_keys" in tables and "key_prefix" in api_key_columns:
        ddl_statements.append("ALTER TABLE api_keys ALTER COLUMN key_prefix TYPE VARCHAR(32)")

    if engine.dialect.name == "postgresql":
        try:
            with engine.connect() as connection:
                result = connection.execute(text(
                    "SELECT c.relname FROM pg_class c "
                    "JOIN pg_namespace n ON n.oid = c.relnamespace "
                    "WHERE n.nspname = 'public' AND c.relrowsecurity = true"
                ))
                rls_enabled_tables = {row[0] for row in result.all()}
                
                policy_result = connection.execute(text(
                    "SELECT tablename FROM pg_policies WHERE schemaname = 'public' AND policyname = 'deny_all'"
                ))
                tables_with_policy = {row[0] for row in policy_result.all()}
        except Exception:
            logger.warning("Failed to query existing RLS status, defaulting to check-and-apply.")
            rls_enabled_tables = set()
            tables_with_policy = set()

        for table in ["users", "analyses", "api_keys", "role_templates"]:
            if table in tables and table not in rls_enabled_tables:
                ddl_statements.append(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            if table in tables and table not in tables_with_policy:
                ddl_statements.append(f"CREATE POLICY \"deny_all\" ON {table} FOR ALL USING (false)")

    if not ddl_statements:
        return

    try:
        with engine.begin() as connection:
            for statement in ddl_statements:
                logger.info("Applying database compatibility DDL: %s", statement)
                connection.execute(text(statement))
    except Exception:
        logger.exception("Failed to apply database compatibility schema updates.")
        raise
