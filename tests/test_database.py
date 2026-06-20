from unittest.mock import MagicMock, patch
from app.utils.database import ensure_database_compatibility

def test_ensure_database_compatibility_postgresql():
    """Verify that ensure_database_compatibility runs PostgreSQL specific ALTER TABLE statements to enable RLS."""
    with patch("app.utils.database.db") as mock_db:
        # Mock engine & dialect
        mock_engine = MagicMock()
        mock_engine.dialect.name = "postgresql"
        mock_db.engine = mock_engine
        
        # Mock inspector
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["users", "analyses", "api_keys", "role_templates"]
        # Mock columns so that the function doesn't think columns are missing
        mock_inspector.get_columns.side_effect = lambda t: [
            {"name": "name"}, {"name": "password_hash"}, {"name": "oauth_provider"},
            {"name": "oauth_id"}, {"name": "created_at"}, {"name": "target_role"},
            {"name": "github_url"}, {"name": "linkedin_url"}, {"name": "key_prefix"},
            {"name": "key_hash"}
        ]
        
        with patch("app.utils.database.inspect", return_value=mock_inspector):
            # Mock connection execution for querying RLS
            mock_conn = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_conn
            
            # Query result for enabled tables (initially empty, i.e., RLS is not yet enabled)
            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_conn.execute.return_value = mock_result
            
            # Connection for executing updates
            mock_begin_conn = MagicMock()
            mock_engine.begin.return_value.__enter__.return_value = mock_begin_conn
            
            ensure_database_compatibility()
            
            # Assert ALTER TABLE statement was executed for each table
            calls = mock_begin_conn.execute.call_args_list
            executed_sqls = [str(call[0][0]) for call in calls]
            
            for table in ["users", "analyses", "api_keys", "role_templates"]:
                expected = f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"
                assert any(expected in sql for sql in executed_sqls), f"Expected RLS to be enabled for {table}"

def test_ensure_database_compatibility_sqlite():
    """Verify that ensure_database_compatibility does not run PostgreSQL specific statements on SQLite."""
    with patch("app.utils.database.db") as mock_db:
        # Mock engine & dialect
        mock_engine = MagicMock()
        mock_engine.dialect.name = "sqlite"
        mock_db.engine = mock_engine
        
        # Mock inspector
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["users", "analyses", "api_keys", "role_templates"]
        mock_inspector.get_columns.side_effect = lambda t: [
            {"name": "name"}, {"name": "password_hash"}, {"name": "oauth_provider"},
            {"name": "oauth_id"}, {"name": "created_at"}, {"name": "target_role"},
            {"name": "github_url"}, {"name": "linkedin_url"}, {"name": "key_prefix"},
            {"name": "key_hash"}
        ]
        
        with patch("app.utils.database.inspect", return_value=mock_inspector):
            ensure_database_compatibility()
            
            # Since no columns are missing and it's SQLite, mock_engine.begin should not be called
            assert not mock_engine.begin.called
