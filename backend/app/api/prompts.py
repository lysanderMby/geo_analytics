from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.schemas import (
    Prompt, PromptCreate, PromptUpdate, 
    PromptGenerationRequest, User
)
from app.database.supabase_client import get_supabase
from app.services.prompt_generation import prompt_generation_service
from supabase import Client
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{user_id}/generate")
async def generate_prompts(
    user_id: str,
    generation_request: PromptGenerationRequest,
    supabase: Client = Depends(get_supabase)
):
    """Generate sector-specific prompts for a user using LLM"""
    try:
        # Get user information
        user_result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = User(**user_result.data[0])
        
        # Generate prompts
        generated_prompts = await prompt_generation_service.generate_sector_prompts(
            user=user,
            api_key=generation_request.api_key,
            provider=generation_request.provider,
            model=generation_request.model,
            max_prompts=generation_request.max_prompts
        )
        
        # Save prompts to database
        saved_prompts = []
        for prompt_data in generated_prompts:
            prompt_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            prompt_record = {
                "id": prompt_id,
                "user_id": user_id,
                "content": prompt_data.content,
                "is_auto_generated": prompt_data.is_auto_generated,
                "category": prompt_data.category,
                "created_at": now,
                "updated_at": now
            }
            
            result = supabase.table("prompts").insert(prompt_record).execute()
            if result.data:
                saved_prompts.append(Prompt(**result.data[0]))
        
        return {
            "message": f"Generated {len(saved_prompts)} prompts",
            "prompts": saved_prompts
        }
        
    except Exception as e:
        logger.error(f"Prompt generation failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=List[Prompt])
async def get_user_prompts(
    user_id: str,
    category: str = None,
    supabase: Client = Depends(get_supabase)
):
    """Get all prompts for a user, optionally filtered by category"""
    try:
        query = supabase.table("prompts").select("*").eq("user_id", user_id)
        
        if category:
            query = query.eq("category", category)
        
        result = query.execute()
        
        return [Prompt(**prompt) for prompt in result.data]
        
    except Exception as e:
        logger.error(f"Failed to get prompts for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}", response_model=Prompt)
async def create_prompt(
    user_id: str,
    prompt_data: PromptCreate,
    supabase: Client = Depends(get_supabase)
):
    """Manually create a prompt"""
    try:
        # Verify user exists
        user_result = supabase.table("users").select("id").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        prompt_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        prompt_record = {
            "id": prompt_id,
            "user_id": user_id,
            "content": prompt_data.content,
            "is_auto_generated": prompt_data.is_auto_generated,
            "category": prompt_data.category,
            "created_at": now,
            "updated_at": now
        }
        
        result = supabase.table("prompts").insert(prompt_record).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create prompt")
        
        return Prompt(**result.data[0])
        
    except Exception as e:
        logger.error(f"Prompt creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}/{prompt_id}", response_model=Prompt)
async def update_prompt(
    user_id: str,
    prompt_id: str,
    prompt_data: PromptUpdate,
    supabase: Client = Depends(get_supabase)
):
    """Update prompt content or category"""
    try:
        # Check if prompt exists and belongs to user
        existing = supabase.table("prompts").select("*").eq("id", prompt_id).eq("user_id", user_id).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        # Prepare update data
        update_data = {}
        for field, value in prompt_data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = supabase.table("prompts").update(update_data).eq("id", prompt_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update prompt")
        
        return Prompt(**result.data[0])
        
    except Exception as e:
        logger.error(f"Prompt update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/{prompt_id}")
async def delete_prompt(
    user_id: str,
    prompt_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Delete a prompt"""
    try:
        result = supabase.table("prompts").delete().eq("id", prompt_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        return {"message": "Prompt deleted successfully"}
        
    except Exception as e:
        logger.error(f"Prompt deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/categories")
async def get_prompt_categories(
    user_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get all unique categories for user's prompts"""
    try:
        result = supabase.table("prompts").select("category").eq("user_id", user_id).execute()
        
        categories = list(set([prompt["category"] for prompt in result.data if prompt["category"]]))
        
        return {"categories": categories}
        
    except Exception as e:
        logger.error(f"Failed to get prompt categories for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/validate")
async def validate_prompts(
    user_id: str,
    prompt_ids: List[str],
    generation_request: PromptGenerationRequest,
    supabase: Client = Depends(get_supabase)
):
    """Validate and refine existing prompts using LLM"""
    try:
        # Get user information
        user_result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = User(**user_result.data[0])
        
        # Get prompts to validate
        if prompt_ids:
            prompts_result = supabase.table("prompts").select("content").eq("user_id", user_id).in_("id", prompt_ids).execute()
        else:
            prompts_result = supabase.table("prompts").select("content").eq("user_id", user_id).execute()
        
        if not prompts_result.data:
            raise HTTPException(status_code=404, detail="No prompts found to validate")
        
        prompt_contents = [p["content"] for p in prompts_result.data]
        
        # Validate prompts
        validated_prompts = await prompt_generation_service.validate_and_refine_prompts(
            prompts=prompt_contents,
            user=user,
            api_key=generation_request.api_key,
            provider=generation_request.provider,
            model=generation_request.model
        )
        
        return {
            "message": f"Validated {len(validated_prompts)} prompts",
            "validated_prompts": [p.content for p in validated_prompts],
            "suggestions": "Consider replacing low-quality prompts with validated versions"
        }
        
    except Exception as e:
        logger.error(f"Prompt validation failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 