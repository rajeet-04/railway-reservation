from supabase import create_client, Client
from app.config import settings

# Supabase client
supabase: Client = None


def get_supabase() -> Client:
    """Get Supabase client"""
    global supabase
    if supabase is None:
        supabase = create_client(settings.supabase_url, settings.supabase_key)
    return supabase


def get_supabase_admin() -> Client:
    """Get Supabase admin client with service role key"""
    return create_client(settings.supabase_url, settings.supabase_service_key)
