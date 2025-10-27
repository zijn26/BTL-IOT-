# DB connection
# app/core/database.py
from supabase import create_client, Client
from app.config import settings

# Supabase clients
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
supabase_admin: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
TAG = "DATABASE:-"
class Database:
    def __init__(self):
        self.client = supabase
        self.admin_client = supabase_admin
    
    def execute_query(self, table: str, operation: str, data: dict = None, filters: dict = None):
        """Generic database operation"""
        try:
            query = self.admin_client.table(table)
            
            if operation == "insert":
                result = query.insert(data).execute()
            elif operation == "select":
                query = query.select("*")
                if filters:
                    for key, value in filters.items():
                        query = query.eq(key, value)
                result = query.execute()
            elif operation == "update":
                query = query.update(data)
                if filters:
                    for key, value in filters.items():
                        query = query.eq(key, value)
                result = query.execute()
            elif operation == "delete":
                query = query.delete()
                if filters:
                    for k, v in filters.items():
                        query = query.eq(k, v)
                else:
                    # phòng trường hợp gọi xóa mà không truyền filter: chặn lại
                    raise ValueError("❌ Delete requires at least one filter to avoid deleting entire table")
                result = query.execute()
            return result.data
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return None

# Global database instance
db = Database()
