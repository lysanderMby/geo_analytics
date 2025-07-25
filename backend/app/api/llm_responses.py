from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any
from app.models.schemas import (
    LLMResponse, LLMResponseCreate, BulkPromptTest, 
    BulkTestStatus, LLMConfiguration, User, Prompt
)
from app.database.supabase_client import get_supabase
from app.services.llm_service import llm_service
from supabase import Client
import logging
import uuid
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{user_id}/test-prompt")
async def test_single_prompt(
    user_id: str,
    prompt_id: str,
    configurations: List[LLMConfiguration],
    api_keys: Dict[str, str],  # provider -> api_key mapping
    iterations: int = 20,
    supabase: Client = Depends(get_supabase)
):
    """Test a single prompt against specified LLM configurations"""
    try:
        # Verify user exists
        user_result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get prompt
        prompt_result = supabase.table("prompts").select("*").eq("id", prompt_id).eq("user_id", user_id).execute()
        if not prompt_result.data:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        prompt = Prompt(**prompt_result.data[0])
        
        # Generate responses
        responses = await llm_service.batch_generate_responses(
            configurations=configurations,
            prompt=prompt.content,
            api_keys=api_keys,
            iterations=iterations
        )
        
        # Save responses to database
        saved_responses = []
        for response_data in responses:
            response_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            response_record = {
                "id": response_id,
                "user_id": user_id,
                "prompt_id": prompt_id,
                "provider": response_data["provider"],
                "model": response_data["model"],
                "response_content": response_data["content"],
                "response_metadata": response_data.get("usage", {}),
                "created_at": now
            }
            
            result = supabase.table("llm_responses").insert(response_record).execute()
            if result.data:
                saved_responses.append(LLMResponse(**result.data[0]))
        
        return {
            "message": f"Generated {len(saved_responses)} responses for prompt",
            "prompt": prompt.content,
            "responses": saved_responses
        }
        
    except Exception as e:
        logger.error(f"Single prompt test failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/bulk-test")
async def start_bulk_test(
    user_id: str,
    bulk_test: BulkPromptTest,
    api_keys: Dict[str, str],
    background_tasks: BackgroundTasks,
    supabase: Client = Depends(get_supabase)
):
    """Start a bulk test of multiple prompts against multiple models"""
    try:
        # Verify user exists
        user_result = supabase.table("users").select("id").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify prompts exist
        prompts_result = supabase.table("prompts").select("*").eq("user_id", user_id).in_("id", bulk_test.prompt_ids).execute()
        if len(prompts_result.data) != len(bulk_test.prompt_ids):
            raise HTTPException(status_code=404, detail="Some prompts not found")
        
        # Create test record
        test_id = str(uuid.uuid4())
        total_tests = len(bulk_test.prompt_ids) * len(bulk_test.configurations) * bulk_test.iterations_per_prompt
        
        test_record = {
            "id": test_id,
            "user_id": user_id,
            "status": "pending",
            "total_tests": total_tests,
            "completed_tests": 0,
            "failed_tests": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("bulk_tests").insert(test_record).execute()
        
        # Start background task
        background_tasks.add_task(
            _execute_bulk_test,
            test_id=test_id,
            user_id=user_id,
            prompts_data=prompts_result.data,
            configurations=bulk_test.configurations,
            api_keys=api_keys,
            iterations=bulk_test.iterations_per_prompt,
            supabase=supabase
        )
        
        return {
            "test_id": test_id,
            "message": f"Started bulk test with {total_tests} total operations",
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Bulk test start failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/bulk-test/{test_id}", response_model=BulkTestStatus)
async def get_bulk_test_status(
    user_id: str,
    test_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get status of a bulk test"""
    try:
        result = supabase.table("bulk_tests").select("*").eq("id", test_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Bulk test not found")
        
        test_data = result.data[0]
        
        # Get responses if test is completed
        responses = []
        if test_data["status"] == "completed":
            responses_result = supabase.table("llm_responses").select("*").eq("user_id", user_id).execute()
            # Filter responses that belong to this test (you might want to add a test_id field)
            responses = [LLMResponse(**resp) for resp in responses_result.data]
        
        return BulkTestStatus(
            test_id=test_id,
            status=test_data["status"],
            total_tests=test_data["total_tests"],
            completed_tests=test_data["completed_tests"],
            failed_tests=test_data["failed_tests"],
            estimated_completion=test_data.get("estimated_completion"),
            results=responses if test_data["status"] == "completed" else None
        )
        
    except Exception as e:
        logger.error(f"Failed to get bulk test status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/responses", response_model=List[LLMResponse])
async def get_user_responses(
    user_id: str,
    prompt_id: str = None,
    provider: str = None,
    model: str = None,
    limit: int = 100,
    supabase: Client = Depends(get_supabase)
):
    """Get LLM responses for a user with optional filtering"""
    try:
        query = supabase.table("llm_responses").select("*").eq("user_id", user_id)
        
        if prompt_id:
            query = query.eq("prompt_id", prompt_id)
        if provider:
            query = query.eq("provider", provider)
        if model:
            query = query.eq("model", model)
        
        query = query.limit(limit).order("created_at", desc=True)
        result = query.execute()
        
        return [LLMResponse(**response) for response in result.data]
        
    except Exception as e:
        logger.error(f"Failed to get responses for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/responses/{response_id}", response_model=LLMResponse)
async def get_response(
    user_id: str,
    response_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get a specific LLM response"""
    try:
        result = supabase.table("llm_responses").select("*").eq("id", response_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Response not found")
        
        return LLMResponse(**result.data[0])
        
    except Exception as e:
        logger.error(f"Failed to get response {response_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/responses/{response_id}")
async def delete_response(
    user_id: str,
    response_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Delete an LLM response"""
    try:
        result = supabase.table("llm_responses").delete().eq("id", response_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Response not found")
        
        return {"message": "Response deleted successfully"}
        
    except Exception as e:
        logger.error(f"Response deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _execute_bulk_test(
    test_id: str,
    user_id: str,
    prompts_data: List[Dict],
    configurations: List[LLMConfiguration],
    api_keys: Dict[str, str],
    iterations: int,
    supabase: Client
):
    """Background task to execute bulk test"""
    try:
        # Update status to running
        supabase.table("bulk_tests").update({"status": "running"}).eq("id", test_id).execute()
        
        completed_tests = 0
        failed_tests = 0
        
        for prompt_data in prompts_data:
            prompt_content = prompt_data["content"]
            prompt_id = prompt_data["id"]
            
            try:
                # Generate responses for this prompt
                responses = await llm_service.batch_generate_responses(
                    configurations=configurations,
                    prompt=prompt_content,
                    api_keys=api_keys,
                    iterations=iterations
                )
                
                # Save responses
                for response_data in responses:
                    try:
                        response_id = str(uuid.uuid4())
                        now = datetime.utcnow().isoformat()
                        
                        response_record = {
                            "id": response_id,
                            "user_id": user_id,
                            "prompt_id": prompt_id,
                            "provider": response_data["provider"],
                            "model": response_data["model"],
                            "response_content": response_data["content"],
                            "response_metadata": response_data.get("usage", {}),
                            "created_at": now
                        }
                        
                        supabase.table("llm_responses").insert(response_record).execute()
                        completed_tests += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to save response: {e}")
                        failed_tests += 1
                
            except Exception as e:
                logger.error(f"Failed to generate responses for prompt {prompt_id}: {e}")
                failed_tests += len(configurations) * iterations
            
            # Update progress
            supabase.table("bulk_tests").update({
                "completed_tests": completed_tests,
                "failed_tests": failed_tests
            }).eq("id", test_id).execute()
        
        # Mark as completed
        supabase.table("bulk_tests").update({
            "status": "completed",
            "completed_tests": completed_tests,
            "failed_tests": failed_tests
        }).eq("id", test_id).execute()
        
        logger.info(f"Bulk test {test_id} completed: {completed_tests} successful, {failed_tests} failed")
        
    except Exception as e:
        logger.error(f"Bulk test {test_id} failed: {e}")
        supabase.table("bulk_tests").update({"status": "failed"}).eq("id", test_id).execute() 