import asyncio
import logging
from typing import List, Dict, Any, Optional
import openai
import anthropic
import google.generativeai as genai
from app.models.schemas import LLMProvider, LLMConfiguration
import httpx
import json

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.clients = {}
    
    def _initialize_client(self, provider: LLMProvider, api_key: str):
        """Initialize the appropriate LLM client"""
        if provider == LLMProvider.OPENAI:
            return openai.AsyncOpenAI(api_key=api_key)
        elif provider == LLMProvider.ANTHROPIC:
            return anthropic.AsyncAnthropic(api_key=api_key)
        elif provider == LLMProvider.GEMINI:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-pro')
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    async def generate_response(
        self, 
        provider: LLMProvider, 
        model: str, 
        prompt: str, 
        api_key: str,
        system_message: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate a response from the specified LLM"""
        try:
            if provider == LLMProvider.OPENAI:
                client = openai.AsyncOpenAI(api_key=api_key)
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})
                
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                return {
                    "content": response.choices[0].message.content,
                    "usage": response.usage.dict() if response.usage else {},
                    "model": model,
                    "provider": provider
                }
            
            elif provider == LLMProvider.ANTHROPIC:
                client = anthropic.AsyncAnthropic(api_key=api_key)
                
                full_prompt = prompt
                if system_message:
                    full_prompt = f"{system_message}\n\nHuman: {prompt}\n\nAssistant:"
                else:
                    full_prompt = f"Human: {prompt}\n\nAssistant:"
                
                response = await client.completions.create(
                    model=model,
                    prompt=full_prompt,
                    max_tokens_to_sample=max_tokens,
                    temperature=temperature
                )
                
                return {
                    "content": response.completion,
                    "usage": {"completion_tokens": len(response.completion.split())},
                    "model": model,
                    "provider": provider
                }
            
            elif provider == LLMProvider.GEMINI:
                genai.configure(api_key=api_key)
                model_instance = genai.GenerativeModel(model)
                
                full_prompt = prompt
                if system_message:
                    full_prompt = f"{system_message}\n\n{prompt}"
                
                response = await model_instance.generate_content_async(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=temperature,
                    )
                )
                
                return {
                    "content": response.text,
                    "usage": {"completion_tokens": len(response.text.split())},
                    "model": model,
                    "provider": provider
                }
                
        except Exception as e:
            logger.error(f"Error generating response from {provider}/{model}: {e}")
            raise
    
    async def batch_generate_responses(
        self,
        configurations: List[LLMConfiguration],
        prompt: str,
        api_keys: Dict[LLMProvider, str],
        iterations: int = 1,
        system_message: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate multiple responses across different models and iterations"""
        tasks = []
        
        for config in configurations:
            if not config.is_active:
                continue
                
            api_key = api_keys.get(config.provider)
            if not api_key:
                logger.warning(f"No API key provided for {config.provider}")
                continue
            
            for _ in range(iterations):
                task = self.generate_response(
                    provider=config.provider,
                    model=config.model,
                    prompt=prompt,
                    api_key=api_key,
                    system_message=system_message
                )
                tasks.append(task)
        
        try:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            successful_responses = []
            
            for response in responses:
                if isinstance(response, Exception):
                    logger.error(f"Response generation failed: {response}")
                    continue
                successful_responses.append(response)
            
            return successful_responses
            
        except Exception as e:
            logger.error(f"Batch response generation failed: {e}")
            raise

    async def web_search(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """Perform web search (simplified implementation)"""
        # This is a placeholder - in production, you'd use a proper search API
        # like Google Custom Search, Bing Search API, or SerpAPI
        logger.info(f"Performing web search for: {query}")
        
        # Placeholder results
        return [
            {
                "title": f"Search result {i+1} for {query}",
                "url": f"https://example{i+1}.com",
                "snippet": f"This is a snippet about {query} from result {i+1}"
            }
            for i in range(min(num_results, 5))
        ]
    
    async def analyze_website(self, url: str, api_key: str, provider: LLMProvider) -> Dict[str, Any]:
        """Analyze a website using LLM"""
        try:
            # Simple web scraping (in production, use proper scraping tools)
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    content = response.text[:2000]  # Limit content length
                else:
                    content = f"Unable to access website: {url}"
            
            analysis_prompt = f"""
            Analyze this website content and extract key business information:
            
            Website: {url}
            Content: {content}
            
            Please provide:
            1. Business name
            2. Industry/sector
            3. Key products/services
            4. Target market
            5. Geographic focus
            
            Format as JSON.
            """
            
            result = await self.generate_response(
                provider=provider,
                model="gpt-3.5-turbo" if provider == LLMProvider.OPENAI else "claude-3-haiku",
                prompt=analysis_prompt,
                api_key=api_key
            )
            
            return {
                "analysis": result["content"],
                "url": url,
                "scraped_content_preview": content[:500]
            }
            
        except Exception as e:
            logger.error(f"Website analysis failed for {url}: {e}")
            return {
                "analysis": f"Failed to analyze website: {str(e)}",
                "url": url,
                "scraped_content_preview": ""
            }

# Global service instance
llm_service = LLMService() 