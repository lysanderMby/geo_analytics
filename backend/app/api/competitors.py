from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List
from app.models.schemas import (
    Competitor, CompetitorCreate, CompetitorUpdate, 
    CompetitorDiscoveryRequest, User, LLMProvider
)
from app.database.supabase_client import get_supabase
from app.services.competitor_discovery import competitor_discovery_service
from supabase import Client
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{user_id}/discover")
async def discover_competitors(
    user_id: str,
    discovery_request: CompetitorDiscoveryRequest,
    background_tasks: BackgroundTasks,
    supabase: Client = Depends(get_supabase)
):
    """Discover competitors for a user using LLM analysis"""
    try:
        # Get user information
        user_result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = User(**user_result.data[0])
        
        # Discover competitors
        discovered_competitors = await competitor_discovery_service.discover_competitors(
            user=user,
            api_key=discovery_request.api_key,
            provider=discovery_request.provider,
            model=discovery_request.model
        )
        
        # Save competitors to database
        saved_competitors = []
        for comp_data in discovered_competitors:
            competitor_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            competitor_record = {
                "id": competitor_id,
                "user_id": user_id,
                "name": comp_data.name,
                "website": str(comp_data.website) if comp_data.website else None,
                "description": comp_data.description,
                "is_auto_discovered": comp_data.is_auto_discovered,
                "created_at": now,
                "updated_at": now
            }
            
            result = supabase.table("competitors").insert(competitor_record).execute()
            if result.data:
                saved_competitors.append(Competitor(**result.data[0]))
        
        return {
            "message": f"Discovered {len(saved_competitors)} competitors",
            "competitors": saved_competitors
        }
        
    except Exception as e:
        logger.error(f"Competitor discovery failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=List[Competitor])
async def get_user_competitors(
    user_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get all competitors for a user"""
    try:
        result = supabase.table("competitors").select("*").eq("user_id", user_id).execute()
        
        return [Competitor(**comp) for comp in result.data]
        
    except Exception as e:
        logger.error(f"Failed to get competitors for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}", response_model=Competitor)
async def create_competitor(
    user_id: str,
    competitor_data: CompetitorCreate,
    supabase: Client = Depends(get_supabase)
):
    """Manually add a competitor"""
    try:
        # Verify user exists
        user_result = supabase.table("users").select("id").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        competitor_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        competitor_record = {
            "id": competitor_id,
            "user_id": user_id,
            "name": competitor_data.name,
            "website": str(competitor_data.website) if competitor_data.website else None,
            "description": competitor_data.description,
            "is_auto_discovered": competitor_data.is_auto_discovered,
            "created_at": now,
            "updated_at": now
        }
        
        result = supabase.table("competitors").insert(competitor_record).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create competitor")
        
        return Competitor(**result.data[0])
        
    except Exception as e:
        logger.error(f"Competitor creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}/{competitor_id}", response_model=Competitor)
async def update_competitor(
    user_id: str,
    competitor_id: str,
    competitor_data: CompetitorUpdate,
    supabase: Client = Depends(get_supabase)
):
    """Update competitor information"""
    try:
        # Check if competitor exists and belongs to user
        existing = supabase.table("competitors").select("*").eq("id", competitor_id).eq("user_id", user_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        # Prepare update data
        update_data = {}
        for field, value in competitor_data.dict(exclude_unset=True).items():
            if value is not None:
                if field == "website" and value:
                    update_data[field] = str(value)
                else:
                    update_data[field] = value
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = supabase.table("competitors").update(update_data).eq("id", competitor_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update competitor")
        
        return Competitor(**result.data[0])
        
    except Exception as e:
        logger.error(f"Competitor update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/{competitor_id}")
async def delete_competitor(
    user_id: str,
    competitor_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Delete a competitor"""
    try:
        result = supabase.table("competitors").delete().eq("id", competitor_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Competitor not found")
        
        return {"message": "Competitor deleted successfully"}
        
    except Exception as e:
        logger.error(f"Competitor deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/refine")
async def refine_competitors(
    user_id: str,
    discovery_request: CompetitorDiscoveryRequest,
    supabase: Client = Depends(get_supabase)
):
    """Refine competitor list based on existing competitors"""
    try:
        # Get user information
        user_result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = User(**user_result.data[0])
        
        # Get existing competitors
        existing_result = supabase.table("competitors").select("name").eq("user_id", user_id).execute()
        existing_competitors = [comp["name"] for comp in existing_result.data]
        
        if not existing_competitors:
            raise HTTPException(status_code=400, detail="No existing competitors to refine from")
        
        # Refine competitor list
        additional_competitors = await competitor_discovery_service.refine_competitor_list(
            user=user,
            existing_competitors=existing_competitors,
            api_key=discovery_request.api_key,
            provider=discovery_request.provider,
            model=discovery_request.model
        )
        
        # Save additional competitors
        saved_competitors = []
        for comp_data in additional_competitors:
            competitor_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            competitor_record = {
                "id": competitor_id,
                "user_id": user_id,
                "name": comp_data.name,
                "website": str(comp_data.website) if comp_data.website else None,
                "description": comp_data.description,
                "is_auto_discovered": comp_data.is_auto_discovered,
                "created_at": now,
                "updated_at": now
            }
            
            result = supabase.table("competitors").insert(competitor_record).execute()
            if result.data:
                saved_competitors.append(Competitor(**result.data[0]))
        
        return {
            "message": f"Added {len(saved_competitors)} additional competitors",
            "competitors": saved_competitors
        }
        
    except Exception as e:
        logger.error(f"Competitor refinement failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 