#!/usr/bin/env python3
"""
Test database connection
"""
import os
import sys
from dotenv import load_dotenv

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test database connection"""
    try:
        from app.database import db
        from app.config import settings
        
        print("🔧 Testing configuration...")
        print(f"SUPABASE_URL: {'✅ Set' if settings.SUPABASE_URL else '❌ Missing'}")
        print(f"SUPABASE_ANON_KEY: {'✅ Set' if settings.SUPABASE_ANON_KEY else '❌ Missing'}")
        print(f"SUPABASE_SERVICE_KEY: {'✅ Set' if settings.SUPABASE_SERVICE_KEY else '❌ Missing'}")
        print(f"JWT_SECRET_KEY: {'✅ Set' if settings.JWT_SECRET_KEY else '❌ Missing'}")
        
        if not all([settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY, settings.SUPABASE_SERVICE_KEY]):
            print("\n❌ Missing required environment variables!")
            print("Please set SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_KEY in .env file")
            return False
            
        print("\n🔌 Testing database connection...")
        
        # Test simple query
        result = db.execute_query("users", "select", filters={"limit": 1})
        
        
        if result is not None:
            print("✅ Database connection successful!")
            print(f"Query result: {result}")
            return True
        else:
            print("❌ Database query failed!")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all packages are installed: pip install supabase pydantic-settings python-dotenv")
        return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database connection test...\n")
    success = test_database_connection()
    
    if success:
        print("\n🎉 All tests passed! Database is ready to use.")
    else:
        print("\n💥 Tests failed! Please check your configuration.")
        sys.exit(1)