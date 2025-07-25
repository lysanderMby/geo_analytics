from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.models.schemas import (
    AnalyticsResult, DashboardSummary, CompetitorComparison,
    ModelPerformance, User, Competitor, LLMResponse
)
from app.database.supabase_client import get_supabase
from app.services.analytics_service import analytics_service
from supabase import Client
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{user_id}/analyze-responses")
async def analyze_responses(
    user_id: str,
    response_ids: List[str] = None,
    api_key: str = None,
    supabase: Client = Depends(get_supabase)
):
    """Analyze LLM responses for brand mentions"""
    try:
        # Get user information
        user_result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = User(**user_result.data[0])
        
        # Get competitors
        competitors_result = supabase.table("competitors").select("*").eq("user_id", user_id).execute()
        competitors = [Competitor(**comp) for comp in competitors_result.data]
        
        # Get responses to analyze
        if response_ids:
            responses_result = supabase.table("llm_responses").select("*").eq("user_id", user_id).in_("id", response_ids).execute()
        else:
            # Analyze all unanalyzed responses
            responses_result = supabase.table("llm_responses").select("*").eq("user_id", user_id).execute()
        
        if not responses_result.data:
            raise HTTPException(status_code=404, detail="No responses found to analyze")
        
        responses = [LLMResponse(**resp) for resp in responses_result.data]
        
        # Filter out already analyzed responses
        existing_analysis = supabase.table("analytics").select("llm_response_id").eq("user_id", user_id).execute()
        analyzed_response_ids = {result["llm_response_id"] for result in existing_analysis.data}
        
        responses_to_analyze = [resp for resp in responses if resp.id not in analyzed_response_ids]
        
        if not responses_to_analyze:
            return {"message": "All responses have already been analyzed"}
        
        # Perform analysis
        analytics_results = await analytics_service.batch_analyze_responses(
            user=user,
            competitors=competitors,
            llm_responses=responses_to_analyze,
            api_key=api_key
        )
        
        # Save analytics results
        saved_results = []
        for result in analytics_results:
            analytics_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            analytics_record = {
                "id": analytics_id,
                "user_id": user_id,
                "prompt_id": result.prompt_id,
                "llm_response_id": result.llm_response_id,
                "user_brand_mentions": result.user_brand_mentions,
                "competitor_mentions": result.competitor_mentions,
                "total_mentions": result.total_mentions,
                "mention_details": [mention.dict() for mention in result.mention_details],
                "analysis_metadata": result.analysis_metadata,
                "created_at": now
            }
            
            db_result = supabase.table("analytics").insert(analytics_record).execute()
            if db_result.data:
                saved_results.append(AnalyticsResult(**db_result.data[0]))
        
        return {
            "message": f"Analyzed {len(saved_results)} responses",
            "analytics_results": saved_results
        }
        
    except Exception as e:
        logger.error(f"Analytics processing failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    user_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get dashboard summary for a user"""
    try:
        # Get counts
        prompts_count = len(supabase.table("prompts").select("id").eq("user_id", user_id).execute().data)
        competitors_count = len(supabase.table("competitors").select("id").eq("user_id", user_id).execute().data)
        responses_count = len(supabase.table("llm_responses").select("id").eq("user_id", user_id).execute().data)
        
        # Get analytics results
        analytics_result = supabase.table("analytics").select("*").eq("user_id", user_id).execute()
        analytics_data = [AnalyticsResult(**result) for result in analytics_result.data]
        
        if not analytics_data:
            return DashboardSummary(
                total_prompts=prompts_count,
                total_competitors=competitors_count,
                total_responses=responses_count,
                user_brand_mention_rate=0.0,
                top_competitor_mention_rate=0.0,
                last_analysis_date=None
            )
        
        # Calculate metrics
        metrics = analytics_service.calculate_performance_metrics(analytics_data)
        
        # Find top competitor
        top_competitor_rate = 0.0
        if metrics["top_competitors"]:
            top_competitor_rate = metrics["top_competitors"][0]["mention_rate"]
        
        # Get last analysis date
        last_analysis_date = max([result.created_at for result in analytics_data])
        
        return DashboardSummary(
            total_prompts=prompts_count,
            total_competitors=competitors_count,
            total_responses=responses_count,
            user_brand_mention_rate=metrics["user_mention_rate"],
            top_competitor_mention_rate=top_competitor_rate,
            last_analysis_date=last_analysis_date
        )
        
    except Exception as e:
        logger.error(f"Dashboard summary failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/competitor-comparison", response_model=List[CompetitorComparison])
async def get_competitor_comparison(
    user_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get detailed competitor comparison"""
    try:
        # Get analytics results
        analytics_result = supabase.table("analytics").select("*").eq("user_id", user_id).execute()
        analytics_data = [AnalyticsResult(**result) for result in analytics_result.data]
        
        if not analytics_data:
            return []
        
        # Calculate competitor comparisons
        comparisons = []
        
        # Get all competitors mentioned
        all_competitors = set()
        for result in analytics_data:
            all_competitors.update(result.competitor_mentions.keys())
        
        user_total_mentions = sum(result.user_brand_mentions for result in analytics_data)
        
        for competitor_name in all_competitors:
            competitor_total_mentions = sum(
                result.competitor_mentions.get(competitor_name, 0) 
                for result in analytics_data
            )
            
            # Calculate ratio (user mentions / competitor mentions)
            if competitor_total_mentions > 0:
                mention_ratio = user_total_mentions / competitor_total_mentions
            else:
                mention_ratio = float('inf') if user_total_mentions > 0 else 0
            
            # Determine trend (simplified - you'd need historical data for real trends)
            trend = "stable"
            if mention_ratio > 1.2:
                trend = "up"
            elif mention_ratio < 0.8:
                trend = "down"
            
            comparisons.append(CompetitorComparison(
                competitor_name=competitor_name,
                user_mentions=user_total_mentions,
                competitor_mentions=competitor_total_mentions,
                mention_ratio=mention_ratio,
                trend=trend
            ))
        
        # Sort by competitor mentions (descending)
        comparisons.sort(key=lambda x: x.competitor_mentions, reverse=True)
        
        return comparisons
        
    except Exception as e:
        logger.error(f"Competitor comparison failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/model-performance", response_model=List[ModelPerformance])
async def get_model_performance(
    user_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get performance comparison across different LLM models"""
    try:
        # Get analytics and response data
        analytics_result = supabase.table("analytics").select("*").eq("user_id", user_id).execute()
        responses_result = supabase.table("llm_responses").select("*").eq("user_id", user_id).execute()
        
        analytics_data = [AnalyticsResult(**result) for result in analytics_result.data]
        responses_data = [LLMResponse(**resp) for resp in responses_result.data]
        
        if not analytics_data or not responses_data:
            return []
        
        # Use analytics service to compare model performance
        model_comparison = analytics_service.compare_model_performance(analytics_data, responses_data)
        
        # Convert to ModelPerformance objects
        performance_list = []
        for model_key, metrics in model_comparison.items():
            provider, model = model_key.split("_", 1)
            
            performance_list.append(ModelPerformance(
                provider=provider,
                model=model,
                total_responses=metrics["total_responses"],
                user_brand_mentions=sum(
                    result.user_brand_mentions 
                    for result in analytics_data 
                    if any(resp.id == result.llm_response_id and f"{resp.provider}_{resp.model}" == model_key 
                           for resp in responses_data)
                ),
                mention_rate=metrics["user_mention_rate"],
                avg_response_time=None  # Would need to track this in response metadata
            ))
        
        # Sort by mention rate (descending)
        performance_list.sort(key=lambda x: x.mention_rate, reverse=True)
        
        return performance_list
        
    except Exception as e:
        logger.error(f"Model performance analysis failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/analytics/{analytics_id}", response_model=AnalyticsResult)
async def get_analytics_result(
    user_id: str,
    analytics_id: str,
    supabase: Client = Depends(get_supabase)
):
    """Get detailed analytics result"""
    try:
        result = supabase.table("analytics").select("*").eq("id", analytics_id).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Analytics result not found")
        
        return AnalyticsResult(**result.data[0])
        
    except Exception as e:
        logger.error(f"Failed to get analytics result {analytics_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/search")
async def search_responses(
    user_id: str,
    query: str,
    supabase: Client = Depends(get_supabase)
):
    """Search through LLM responses for specific content"""
    try:
        # This is a simplified search - in production you'd use full-text search
        responses_result = supabase.table("llm_responses").select("*").eq("user_id", user_id).execute()
        
        matching_responses = []
        for response_data in responses_result.data:
            if query.lower() in response_data["response_content"].lower():
                matching_responses.append(LLMResponse(**response_data))
        
        return {
            "query": query,
            "matches_found": len(matching_responses),
            "responses": matching_responses[:20]  # Limit results
        }
        
    except Exception as e:
        logger.error(f"Search failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 