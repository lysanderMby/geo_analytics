import json
import logging
from typing import List, Dict, Any
from app.models.schemas import LLMProvider, CompetitorCreate, User
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

class CompetitorDiscoveryService:
    
    async def discover_competitors(
        self,
        user: User,
        api_key: str,
        provider: LLMProvider,
        model: str = None
    ) -> List[CompetitorCreate]:
        """Discover competitors for a user's business using LLM and web search"""
        
        try:
            # Default models if not specified
            if not model:
                if provider == LLMProvider.OPENAI:
                    model = "gpt-4"
                elif provider == LLMProvider.ANTHROPIC:
                    model = "claude-3-sonnet"
                elif provider == LLMProvider.GEMINI:
                    model = "gemini-pro"
            
            # First, analyze the user's website
            website_analysis = await llm_service.analyze_website(
                url=str(user.website),
                api_key=api_key,
                provider=provider
            )
            
            # Perform web searches for potential competitors
            search_queries = [
                f"{user.sector} companies {user.location}",
                f"best {user.sector} businesses {user.location}",
                f"{user.business_name} competitors",
                f"top {user.sector} services {user.location}",
                f"alternatives to {user.business_name}"
            ]
            
            search_results = []
            for query in search_queries:
                results = await llm_service.web_search(query, num_results=5)
                search_results.extend(results)
            
            # Use LLM to analyze and identify competitors
            competitor_analysis_prompt = f"""
            You are a business analyst tasked with identifying competitors for a business.
            
            Business Information:
            - Name: {user.business_name}
            - Website: {user.website}
            - Sector: {user.sector}
            - Location: {user.location}
            - Size: {user.business_size}
            - Description: {user.description or 'Not provided'}
            
            Website Analysis:
            {website_analysis.get('analysis', 'No analysis available')}
            
            Web Search Results:
            {json.dumps(search_results, indent=2)}
            
            Based on this information, identify the top 10-15 most relevant competitors. 
            For each competitor, provide:
            1. Company name
            2. Website URL (if available)
            3. Brief description of why they're a competitor
            4. Geographic overlap (local, regional, national, global)
            5. Business size estimate
            
            Return ONLY a JSON array with this structure:
            [
              {
                "name": "Competitor Name",
                "website": "https://competitor.com",
                "description": "Brief description of why they're a competitor",
                "geographic_overlap": "local|regional|national|global",
                "estimated_size": "startup|small|medium|large|enterprise"
              }
            ]
            
            Focus on direct competitors who serve the same market and customer base.
            Exclude suppliers, partners, or businesses in different market segments.
            """
            
            response = await llm_service.generate_response(
                provider=provider,
                model=model,
                prompt=competitor_analysis_prompt,
                api_key=api_key,
                max_tokens=2000,
                temperature=0.3  # Lower temperature for more consistent output
            )
            
            # Parse the LLM response
            competitors_data = self._parse_competitors_response(response["content"])
            
            # Convert to CompetitorCreate objects
            competitors = []
            for comp_data in competitors_data:
                competitor = CompetitorCreate(
                    name=comp_data.get("name", "Unknown"),
                    website=comp_data.get("website") if comp_data.get("website") else None,
                    description=f"{comp_data.get('description', '')} | Geographic overlap: {comp_data.get('geographic_overlap', 'unknown')} | Estimated size: {comp_data.get('estimated_size', 'unknown')}",
                    is_auto_discovered=True
                )
                competitors.append(competitor)
            
            logger.info(f"Discovered {len(competitors)} competitors for {user.business_name}")
            return competitors
            
        except Exception as e:
            logger.error(f"Competitor discovery failed for user {user.id}: {e}")
            raise
    
    def _parse_competitors_response(self, response_content: str) -> List[Dict[str, Any]]:
        """Parse the LLM response and extract competitor data"""
        try:
            # Try to extract JSON from the response
            content = response_content.strip()
            
            # Look for JSON array in the response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_content = content[start_idx:end_idx]
                competitors_data = json.loads(json_content)
                
                # Validate and clean the data
                valid_competitors = []
                for comp in competitors_data:
                    if isinstance(comp, dict) and comp.get("name"):
                        valid_competitors.append(comp)
                
                return valid_competitors
            else:
                logger.warning("No valid JSON array found in LLM response")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse competitor JSON: {e}")
            logger.debug(f"Response content: {response_content}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing competitors response: {e}")
            return []
    
    async def refine_competitor_list(
        self,
        user: User,
        existing_competitors: List[str],
        api_key: str,
        provider: LLMProvider,
        model: str = None
    ) -> List[CompetitorCreate]:
        """Refine and expand the competitor list based on existing competitors"""
        
        try:
            if not model:
                if provider == LLMProvider.OPENAI:
                    model = "gpt-3.5-turbo"
                elif provider == LLMProvider.ANTHROPIC:
                    model = "claude-3-haiku"
                elif provider == LLMProvider.GEMINI:
                    model = "gemini-pro"
            
            refinement_prompt = f"""
            You are analyzing competitors for {user.business_name} in the {user.sector} sector.
            
            Current competitor list:
            {json.dumps(existing_competitors, indent=2)}
            
            Business details:
            - Sector: {user.sector}
            - Location: {user.location}
            - Size: {user.business_size}
            
            Based on the existing competitors, identify 5-10 additional competitors that might have been missed.
            Focus on:
            1. Companies similar to the existing ones
            2. Indirect competitors who might compete for the same customers
            3. Emerging players in the space
            4. Larger companies with competing divisions
            
            Return a JSON array with the same structure as before.
            """
            
            response = await llm_service.generate_response(
                provider=provider,
                model=model,
                prompt=refinement_prompt,
                api_key=api_key,
                max_tokens=1500,
                temperature=0.4
            )
            
            additional_competitors_data = self._parse_competitors_response(response["content"])
            
            additional_competitors = []
            for comp_data in additional_competitors_data:
                competitor = CompetitorCreate(
                    name=comp_data.get("name", "Unknown"),
                    website=comp_data.get("website") if comp_data.get("website") else None,
                    description=f"[Refined Discovery] {comp_data.get('description', '')}",
                    is_auto_discovered=True
                )
                additional_competitors.append(competitor)
            
            return additional_competitors
            
        except Exception as e:
            logger.error(f"Competitor refinement failed: {e}")
            return []

# Global service instance
competitor_discovery_service = CompetitorDiscoveryService() 