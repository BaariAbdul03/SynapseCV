import sys
from sqlalchemy import create_engine, text

def main():
    """
    Applies Row Level Security (RLS) directly to the Supabase PostgreSQL database tables.
    Usage: python apply_rls.py <DATABASE_URL>
    """
    if len(sys.argv) < 2:
        print("Usage: python apply_rls.py <DATABASE_URL>")
        sys.exit(1)
        
    db_url = sys.argv[1]
    # Standard replacement for older postgres URLs
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    print("Connecting to database...")
    try:
        engine = create_engine(db_url)
        with engine.begin() as connection:
            # Query tables in the public schema that already have RLS enabled
            result = connection.execute(text(
                "SELECT c.relname FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' AND c.relrowsecurity = true"
            ))
            rls_enabled_tables = {row[0] for row in result.all()}
            
            print("Enabling Row Level Security (RLS) on public tables...")
            for table in ["users", "analyses", "api_keys", "role_templates"]:
                if table in rls_enabled_tables:
                    print(f"Table '{table}' already has RLS enabled. Skipping.")
                else:
                    sql = f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"
                    print(f"Executing: {sql}")
                    connection.execute(text(sql))
                
                # Check for existing 'deny_all' policy
                policy_check = text(f"SELECT 1 FROM pg_policies WHERE tablename = :table AND policyname = 'deny_all'")
                has_policy = connection.execute(policy_check, {"table": table}).fetchone()
                
                if not has_policy:
                    policy_sql = f"CREATE POLICY \"deny_all\" ON {table} FOR ALL USING (false)"
                    print(f"Executing: {policy_sql}")
                    connection.execute(text(policy_sql))
                    
            print("\nSuccessfully updated Supabase Row Level Security configurations!")
    except Exception as e:
        print(f"\nError applying RLS: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
