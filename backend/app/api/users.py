from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.schemas import User, UserCreate, UserUpdate
from app.database.supabase_client import get_supabase
from supabase import Client
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=User)
async def create_user(
    user_data: UserCreate,
    supabase: Client = Depends(get_supabase)
):
    """Create a new user account"""
    try:
        # Check if user already exists
        existing = supabase.table("users").select("*").eq("email", user_data.email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create new user
        user_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        user_record = {
            "id": user_id,
            "email": user_data.email,
            "business_name": user_data.business_name,
            "website": str(user_data.website),
            "sector": user_data.sector,
            "business_size": user_data.business_size,
            "location": user_data.location,
            "description": user_data.description,
            "created_at": now,
            "updated_at": now
        }
        
        result = supabase.table("users").insert(user_record).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        return User(**result.data[0])
        
    except Exception as e:
        logger.error(f"User creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get user by ID"""
    try:
        result = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return User(**result.data[0])
        
    except Exception as e:
        logger.error(f"Failed to get user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    supabase: Client = Depends(get_supabase)
):
    """Update user information"""
    try:
        # Check if user exists
        existing = supabase.table("users").select("*").eq("id", user_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prepare update data
        update_data = {}
        for field, value in user_data.dict(exclude_unset=True).items():
            if value is not None:
                if field == "website" and value:
                    update_data[field] = str(value)
                else:
                    update_data[field] = value
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update user")
        
        return User(**result.data[0])
        
    except Exception as e:
        logger.error(f"User update failed for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Delete user and all associated data"""
    try:
        # Note: In production, you might want to soft delete or archive instead
        result = supabase.table("users").delete().eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"message": "User deleted successfully"}
        
    except Exception as e:
        logger.error(f"User deletion failed for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email/{email}", response_model=User)
async def get_user_by_email(
    email: str,
    supabase: Client = Depends(get_supabase)
):
    """Get user by email address"""
    try:
        result = supabase.table("users").select("*").eq("email", email).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return User(**result.data[0])
        
    except Exception as e:
        logger.error(f"Failed to get user by email {email}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 