from supabase import create_client, Client
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self):
        self.client: Client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Supabase client"""
        try:
            self.client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    def get_client(self) -> Client:
        """Get the Supabase client instance"""
        if not self.client:
            self._initialize_client()
        return self.client
    
    async def health_check(self) -> bool:
        """Check if the database connection is healthy"""
        try:
            # Simple query to test connection
            result = self.client.table("users").select("count").execute()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Global instance
supabase_client = SupabaseClient()

def get_supabase() -> Client:
    """Dependency to get Supabase client"""
    return supabase_client.get_client() 