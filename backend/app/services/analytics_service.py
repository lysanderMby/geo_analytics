import re
import logging
from typing import List, Dict, Any, Optional
from collections import Counter
import asyncio
from app.models.schemas import (
    AnalyticsResult, BrandMention, LLMResponse, 
    User, Competitor, LLMProvider
)
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

class AnalyticsService:
    
    def __init__(self):
        # Common words to exclude from brand matching
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'is', 'are', 'was', 'were',
            'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'restaurant', 'company',
            'business', 'service', 'shop', 'store', 'best', 'good', 'great', 'near',
            'me', 'my', 'you', 'your', 'they', 'their', 'them', 'we', 'our', 'us'
        }
    
    async def analyze_response(
        self,
        user: User,
        competitors: List[Competitor],
        llm_response: LLMResponse,
        api_key: str = None,
        enhanced_analysis: bool = True
    ) -> AnalyticsResult:
        """Analyze an LLM response for brand mentions"""
        
        try:
            response_content = llm_response.response_content.lower()
            
            # Analyze user brand mentions
            user_brand_mentions = self._count_brand_mentions(
                response_content, 
                user.business_name
            )
            
            # Analyze competitor mentions
            competitor_mentions = {}
            competitor_mention_details = []
            
            for competitor in competitors:
                mentions = self._count_brand_mentions(
                    response_content, 
                    competitor.name
                )
                competitor_mentions[competitor.name] = mentions["mention_count"]
                
                if mentions["mention_count"] > 0:
                    competitor_mention_details.append(BrandMention(
                        brand_name=competitor.name,
                        mention_count=mentions["mention_count"],
                        mention_positions=mentions["mention_positions"],
                        context_snippets=mentions["context_snippets"]
                    ))
            
            # Create user brand mention details
            user_mention_details = []
            if user_brand_mentions["mention_count"] > 0:
                user_mention_details.append(BrandMention(
                    brand_name=user.business_name,
                    mention_count=user_brand_mentions["mention_count"],
                    mention_positions=user_brand_mentions["mention_positions"],
                    context_snippets=user_brand_mentions["context_snippets"]
                ))
            
            # Calculate total mentions
            total_mentions = user_brand_mentions["mention_count"] + sum(competitor_mentions.values())
            
            # Enhanced analysis using LLM (optional)
            analysis_metadata = {}
            if enhanced_analysis and api_key:
                analysis_metadata = await self._enhanced_analysis(
                    user=user,
                    competitors=competitors,
                    response_content=llm_response.response_content,
                    api_key=api_key
                )
            
            # Combine all mention details
            all_mention_details = user_mention_details + competitor_mention_details
            
            return AnalyticsResult(
                id="",  # Will be set by database
                user_id=user.id,
                prompt_id=llm_response.prompt_id,
                llm_response_id=llm_response.id,
                user_brand_mentions=user_brand_mentions["mention_count"],
                competitor_mentions=competitor_mentions,
                total_mentions=total_mentions,
                mention_details=all_mention_details,
                analysis_metadata=analysis_metadata,
                created_at=llm_response.created_at
            )
            
        except Exception as e:
            logger.error(f"Analytics processing failed for response {llm_response.id}: {e}")
            raise
    
    def _count_brand_mentions(self, text: str, brand_name: str) -> Dict[str, Any]:
        """Count mentions of a brand name in text with context"""
        
        # Clean and prepare brand name for matching
        clean_brand_name = self._clean_brand_name(brand_name)
        
        if not clean_brand_name or len(clean_brand_name) < 2:
            return {
                "mention_count": 0,
                "mention_positions": [],
                "context_snippets": []
            }
        
        # Create pattern for matching (case insensitive, word boundaries)
        pattern = r'\b' + re.escape(clean_brand_name) + r'\b'
        
        # Find all matches
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        
        mention_positions = [match.start() for match in matches]
        context_snippets = []
        
        # Extract context around each mention
        for match in matches:
            start_pos = max(0, match.start() - 50)
            end_pos = min(len(text), match.end() + 50)
            context = text[start_pos:end_pos].strip()
            
            # Clean up the context snippet
            context = re.sub(r'\s+', ' ', context)
            context_snippets.append(context)
        
        return {
            "mention_count": len(matches),
            "mention_positions": mention_positions,
            "context_snippets": context_snippets
        }
    
    def _clean_brand_name(self, brand_name: str) -> str:
        """Clean brand name for better matching"""
        
        # Remove common business suffixes
        suffixes = [
            'inc', 'llc', 'ltd', 'corp', 'corporation', 'company', 'co',
            'restaurant', 'cafe', 'bar', 'pub', 'grill', 'kitchen',
            'services', 'solutions', 'group', 'international', 'global'
        ]
        
        clean_name = brand_name.lower().strip()
        
        # Remove punctuation except hyphens and apostrophes
        clean_name = re.sub(r'[^\w\s\'-]', ' ', clean_name)
        
        # Remove common suffixes
        words = clean_name.split()
        filtered_words = []
        
        for word in words:
            if word not in suffixes and word not in self.stop_words and len(word) > 1:
                filtered_words.append(word)
        
        return ' '.join(filtered_words)
    
    async def _enhanced_analysis(
        self,
        user: User,
        competitors: List[Competitor],
        response_content: str,
        api_key: str
    ) -> Dict[str, Any]:
        """Use LLM for enhanced analysis of the response"""
        
        try:
            competitor_names = [comp.name for comp in competitors]
            
            analysis_prompt = f"""
            Analyze this AI assistant response for mentions and context about businesses in the {user.sector} sector.
            
            User's Business: {user.business_name}
            Competitors to look for: {', '.join(competitor_names[:10])}  # Limit for prompt length
            
            Response to analyze:
            {response_content[:1500]}  # Limit length
            
            Provide analysis in JSON format:
            {{
                "mentioned_businesses": [list of business names mentioned],
                "user_business_context": "How was the user's business mentioned (positive/negative/neutral/not mentioned)",
                "competitor_context": "Summary of how competitors were mentioned",
                "recommendation_bias": "Does the response seem to favor certain businesses?",
                "geographic_relevance": "Are the mentioned businesses relevant to {user.location}?",
                "response_quality": "How helpful and comprehensive is this response?",
                "sentiment_analysis": {{
                    "user_business_sentiment": "positive/negative/neutral",
                    "overall_sentiment": "positive/negative/neutral"
                }}
            }}
            """
            
            analysis_response = await llm_service.generate_response(
                provider=LLMProvider.OPENAI,  # Use OpenAI for analysis
                model="gpt-3.5-turbo",
                prompt=analysis_prompt,
                api_key=api_key,
                max_tokens=800,
                temperature=0.2  # Low temperature for consistent analysis
            )
            
            # Try to parse the JSON response
            import json
            try:
                analysis_data = json.loads(analysis_response["content"])
                return analysis_data
            except json.JSONDecodeError:
                logger.warning("Could not parse enhanced analysis JSON")
                return {"raw_analysis": analysis_response["content"]}
                
        except Exception as e:
            logger.error(f"Enhanced analysis failed: {e}")
            return {"error": str(e)}
    
    async def batch_analyze_responses(
        self,
        user: User,
        competitors: List[Competitor],
        llm_responses: List[LLMResponse],
        api_key: str = None
    ) -> List[AnalyticsResult]:
        """Analyze multiple LLM responses in batch"""
        
        tasks = []
        for response in llm_responses:
            task = self.analyze_response(
                user=user,
                competitors=competitors,
                llm_response=response,
                api_key=api_key,
                enhanced_analysis=False  # Disable for batch to save tokens
            )
            tasks.append(task)
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful_results = []
            
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Batch analysis failed for response: {result}")
                    continue
                successful_results.append(result)
            
            return successful_results
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            raise
    
    def calculate_performance_metrics(
        self,
        analytics_results: List[AnalyticsResult]
    ) -> Dict[str, Any]:
        """Calculate performance metrics from analytics results"""
        
        if not analytics_results:
            return {
                "total_responses": 0,
                "user_mention_rate": 0.0,
                "average_mentions_per_response": 0.0,
                "top_competitors": [],
                "performance_summary": "No data available"
            }
        
        total_responses = len(analytics_results)
        total_user_mentions = sum(result.user_brand_mentions for result in analytics_results)
        responses_with_user_mentions = sum(1 for result in analytics_results if result.user_brand_mentions > 0)
        
        # Calculate competitor performance
        all_competitor_mentions = Counter()
        for result in analytics_results:
            for competitor, count in result.competitor_mentions.items():
                all_competitor_mentions[competitor] += count
        
        # Top competitors by mentions
        top_competitors = [
            {
                "name": competitor,
                "total_mentions": count,
                "mention_rate": count / total_responses
            }
            for competitor, count in all_competitor_mentions.most_common(10)
        ]
        
        # Performance by model/provider
        model_performance = {}
        
        return {
            "total_responses": total_responses,
            "user_mention_rate": responses_with_user_mentions / total_responses if total_responses > 0 else 0.0,
            "user_mentions_per_response": total_user_mentions / total_responses if total_responses > 0 else 0.0,
            "average_mentions_per_response": sum(result.total_mentions for result in analytics_results) / total_responses if total_responses > 0 else 0.0,
            "top_competitors": top_competitors,
            "total_competitor_mentions": sum(all_competitor_mentions.values()),
            "unique_competitors_mentioned": len(all_competitor_mentions),
            "performance_summary": f"User mentioned in {responses_with_user_mentions}/{total_responses} responses ({responses_with_user_mentions/total_responses*100:.1f}%)"
        }
    
    def compare_model_performance(
        self,
        analytics_results: List[AnalyticsResult],
        llm_responses: List[LLMResponse]
    ) -> Dict[str, Any]:
        """Compare performance across different LLM models"""
        
        # Group results by model
        model_groups = {}
        
        for result in analytics_results:
            # Find corresponding LLM response
            llm_response = next((r for r in llm_responses if r.id == result.llm_response_id), None)
            if not llm_response:
                continue
            
            model_key = f"{llm_response.provider}_{llm_response.model}"
            
            if model_key not in model_groups:
                model_groups[model_key] = []
            
            model_groups[model_key].append(result)
        
        # Calculate metrics for each model
        model_comparison = {}
        
        for model_key, results in model_groups.items():
            metrics = self.calculate_performance_metrics(results)
            model_comparison[model_key] = metrics
        
        return model_comparison

# Global service instance
analytics_service = AnalyticsService() 