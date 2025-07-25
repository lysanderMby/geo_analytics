import json
import logging
from typing import List, Dict, Any
from app.models.schemas import LLMProvider, PromptCreate, User
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

class PromptGenerationService:
    
    async def generate_sector_prompts(
        self,
        user: User,
        api_key: str,
        provider: LLMProvider,
        model: str = None,
        max_prompts: int = 50
    ) -> List[PromptCreate]:
        """Generate relevant prompts for a user's business sector"""
        
        try:
            # Default models if not specified
            if not model:
                if provider == LLMProvider.OPENAI:
                    model = "gpt-4"
                elif provider == LLMProvider.ANTHROPIC:
                    model = "claude-3-sonnet"
                elif provider == LLMProvider.GEMINI:
                    model = "gemini-pro"
            
            # Generate different categories of prompts
            prompt_categories = [
                "local_search",
                "comparison",
                "recommendations",
                "reviews",
                "services",
                "pricing",
                "location_specific",
                "problem_solving",
                "alternatives",
                "quality_questions"
            ]
            
            all_prompts = []
            
            for category in prompt_categories:
                category_prompts = await self._generate_category_prompts(
                    user=user,
                    category=category,
                    api_key=api_key,
                    provider=provider,
                    model=model,
                    prompts_per_category=max_prompts // len(prompt_categories)
                )
                all_prompts.extend(category_prompts)
            
            # If we need more prompts, generate additional ones
            if len(all_prompts) < max_prompts:
                additional_prompts = await self._generate_general_prompts(
                    user=user,
                    api_key=api_key,
                    provider=provider,
                    model=model,
                    num_prompts=max_prompts - len(all_prompts)
                )
                all_prompts.extend(additional_prompts)
            
            # Limit to requested number
            all_prompts = all_prompts[:max_prompts]
            
            logger.info(f"Generated {len(all_prompts)} prompts for {user.business_name}")
            return all_prompts
            
        except Exception as e:
            logger.error(f"Prompt generation failed for user {user.id}: {e}")
            raise
    
    async def _generate_category_prompts(
        self,
        user: User,
        category: str,
        api_key: str,
        provider: LLMProvider,
        model: str,
        prompts_per_category: int = 5
    ) -> List[PromptCreate]:
        """Generate prompts for a specific category"""
        
        category_instructions = {
            "local_search": f"Generate prompts that people would use when searching for {user.sector} services in {user.location}",
            "comparison": f"Generate prompts where people compare different {user.sector} options",
            "recommendations": f"Generate prompts asking for recommendations for {user.sector} services",
            "reviews": f"Generate prompts about finding reviews or ratings for {user.sector} businesses",
            "services": f"Generate prompts asking about specific services offered by {user.sector} businesses",
            "pricing": f"Generate prompts about pricing and costs for {user.sector} services",
            "location_specific": f"Generate prompts specific to {user.location} and nearby areas for {user.sector}",
            "problem_solving": f"Generate prompts where people have problems that {user.sector} businesses solve",
            "alternatives": f"Generate prompts where people look for alternatives or options in {user.sector}",
            "quality_questions": f"Generate prompts about quality, expertise, or credentials in {user.sector}"
        }
        
        instruction = category_instructions.get(category, f"Generate general prompts about {user.sector}")
        
        generation_prompt = f"""
        You are creating search prompts that potential customers might type into AI language models when looking for businesses in the {user.sector} sector.
        
        Business Context:
        - Business: {user.business_name}
        - Sector: {user.sector}
        - Location: {user.location}
        - Business Size: {user.business_size}
        - Description: {user.description or 'Not provided'}
        
        Task: {instruction}
        
        Generate {prompts_per_category} realistic prompts that potential customers might ask. 
        These should be natural language questions or statements that people would actually type.
        
        Examples for a London Indian restaurant:
        - "Best Indian restaurant near me"
        - "Indian food delivery in London"
        - "Where can I get authentic curry in London?"
        - "Indian restaurants with good reviews in my area"
        
        Return ONLY a JSON array of strings:
        ["prompt 1", "prompt 2", "prompt 3", ...]
        
        Make the prompts varied in length and style, from short searches to longer questions.
        Include both generic and location-specific prompts.
        """
        
        try:
            response = await llm_service.generate_response(
                provider=provider,
                model=model,
                prompt=generation_prompt,
                api_key=api_key,
                max_tokens=1000,
                temperature=0.8  # Higher temperature for more varied prompts
            )
            
            prompts_data = self._parse_prompts_response(response["content"])
            
            prompts = []
            for prompt_text in prompts_data:
                prompt = PromptCreate(
                    content=prompt_text,
                    is_auto_generated=True,
                    category=category
                )
                prompts.append(prompt)
            
            return prompts
            
        except Exception as e:
            logger.error(f"Category prompt generation failed for {category}: {e}")
            return []
    
    async def _generate_general_prompts(
        self,
        user: User,
        api_key: str,
        provider: LLMProvider,
        model: str,
        num_prompts: int
    ) -> List[PromptCreate]:
        """Generate additional general prompts"""
        
        general_prompt = f"""
        Generate {num_prompts} additional diverse prompts that customers might use when searching for {user.sector} businesses.
        
        Business: {user.business_name}
        Sector: {user.sector}
        Location: {user.location}
        
        Make these prompts different from typical categories. Include:
        - Emergency or urgent needs
        - Seasonal requests
        - Special occasions
        - Business-to-business inquiries
        - Specific demographic needs
        - Technology-related questions
        - Sustainability/ethical considerations
        
        Return as a JSON array of strings.
        """
        
        try:
            response = await llm_service.generate_response(
                provider=provider,
                model=model,
                prompt=general_prompt,
                api_key=api_key,
                max_tokens=800,
                temperature=0.9
            )
            
            prompts_data = self._parse_prompts_response(response["content"])
            
            prompts = []
            for prompt_text in prompts_data:
                prompt = PromptCreate(
                    content=prompt_text,
                    is_auto_generated=True,
                    category="general"
                )
                prompts.append(prompt)
            
            return prompts
            
        except Exception as e:
            logger.error(f"General prompt generation failed: {e}")
            return []
    
    def _parse_prompts_response(self, response_content: str) -> List[str]:
        """Parse the LLM response and extract prompt strings"""
        try:
            content = response_content.strip()
            
            # Look for JSON array in the response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_content = content[start_idx:end_idx]
                prompts_data = json.loads(json_content)
                
                # Validate and clean the data
                valid_prompts = []
                for prompt in prompts_data:
                    if isinstance(prompt, str) and prompt.strip():
                        # Clean and validate the prompt
                        cleaned_prompt = prompt.strip().strip('"\'')
                        if len(cleaned_prompt) > 5:  # Minimum length check
                            valid_prompts.append(cleaned_prompt)
                
                return valid_prompts
            else:
                logger.warning("No valid JSON array found in prompts response")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse prompts JSON: {e}")
            logger.debug(f"Response content: {response_content}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing prompts response: {e}")
            return []
    
    async def validate_and_refine_prompts(
        self,
        prompts: List[str],
        user: User,
        api_key: str,
        provider: LLMProvider,
        model: str = None
    ) -> List[PromptCreate]:
        """Validate and refine a list of prompts for relevance and quality"""
        
        try:
            if not model:
                model = "gpt-3.5-turbo" if provider == LLMProvider.OPENAI else "claude-3-haiku"
            
            validation_prompt = f"""
            Review these prompts for a {user.sector} business called {user.business_name} in {user.location}.
            
            Prompts to review:
            {json.dumps(prompts, indent=2)}
            
            For each prompt, evaluate:
            1. Is it relevant to the business sector?
            2. Would it potentially return this business in results?
            3. Is it naturally phrased?
            4. Is it specific enough to be useful?
            
            Return only the prompts that pass all criteria, improved if necessary.
            Return as a JSON array of strings.
            """
            
            response = await llm_service.generate_response(
                provider=provider,
                model=model,
                prompt=validation_prompt,
                api_key=api_key,
                max_tokens=1200,
                temperature=0.3
            )
            
            validated_prompts_data = self._parse_prompts_response(response["content"])
            
            validated_prompts = []
            for prompt_text in validated_prompts_data:
                prompt = PromptCreate(
                    content=prompt_text,
                    is_auto_generated=True,
                    category="validated"
                )
                validated_prompts.append(prompt)
            
            return validated_prompts
            
        except Exception as e:
            logger.error(f"Prompt validation failed: {e}")
            # Return original prompts as fallback
            return [PromptCreate(content=p, is_auto_generated=True, category="unvalidated") for p in prompts]

# Global service instance
prompt_generation_service = PromptGenerationService() 