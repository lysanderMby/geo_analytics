from pydantic import BaseModel, EmailStr, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class BusinessSize(str, Enum):
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"

class PromptStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# User Models
class UserCreate(BaseModel):
    email: EmailStr
    business_name: str
    website: HttpUrl
    sector: str
    business_size: BusinessSize
    location: str
    description: Optional[str] = None

class UserUpdate(BaseModel):
    business_name: Optional[str] = None
    website: Optional[HttpUrl] = None
    sector: Optional[str] = None
    business_size: Optional[BusinessSize] = None
    location: Optional[str] = None
    description: Optional[str] = None

class User(BaseModel):
    id: str
    email: EmailStr
    business_name: str
    website: str
    sector: str
    business_size: BusinessSize
    location: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# API Configuration Models
class LLMConfiguration(BaseModel):
    provider: LLMProvider
    model: str
    is_active: bool = True

class APIConfigurationCreate(BaseModel):
    user_id: str
    configurations: List[LLMConfiguration]

class APIConfiguration(BaseModel):
    id: str
    user_id: str
    provider: LLMProvider
    model: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

# Competitor Models
class CompetitorCreate(BaseModel):
    name: str
    website: Optional[HttpUrl] = None
    description: Optional[str] = None
    is_auto_discovered: bool = False

class CompetitorUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[HttpUrl] = None
    description: Optional[str] = None

class Competitor(BaseModel):
    id: str
    user_id: str
    name: str
    website: Optional[str] = None
    description: Optional[str] = None
    is_auto_discovered: bool
    created_at: datetime
    updated_at: datetime

# Prompt Models
class PromptCreate(BaseModel):
    content: str
    is_auto_generated: bool = False
    category: Optional[str] = None

class PromptUpdate(BaseModel):
    content: Optional[str] = None
    category: Optional[str] = None

class Prompt(BaseModel):
    id: str
    user_id: str
    content: str
    is_auto_generated: bool
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# LLM Response Models
class LLMResponseCreate(BaseModel):
    prompt_id: str
    provider: LLMProvider
    model: str
    response_content: str
    response_metadata: Optional[Dict[str, Any]] = None

class LLMResponse(BaseModel):
    id: str
    user_id: str
    prompt_id: str
    provider: LLMProvider
    model: str
    response_content: str
    response_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

# Analytics Models
class BrandMention(BaseModel):
    brand_name: str
    mention_count: int
    mention_positions: List[int]
    context_snippets: List[str]

class AnalyticsResult(BaseModel):
    id: str
    user_id: str
    prompt_id: str
    llm_response_id: str
    user_brand_mentions: int
    competitor_mentions: Dict[str, int]
    total_mentions: int
    mention_details: List[BrandMention]
    analysis_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

# Bulk Operations
class BulkPromptTest(BaseModel):
    prompt_ids: List[str]
    configurations: List[LLMConfiguration]
    iterations_per_prompt: int = 20

class BulkTestStatus(BaseModel):
    test_id: str
    status: PromptStatus
    total_tests: int
    completed_tests: int
    failed_tests: int
    estimated_completion: Optional[datetime] = None
    results: Optional[List[AnalyticsResult]] = None

# Discovery Models
class CompetitorDiscoveryRequest(BaseModel):
    api_key: str  # Will be encrypted/handled securely
    provider: LLMProvider
    model: str

class PromptGenerationRequest(BaseModel):
    api_key: str  # Will be encrypted/handled securely
    provider: LLMProvider
    model: str
    max_prompts: int = 50

# Dashboard Models
class DashboardSummary(BaseModel):
    total_prompts: int
    total_competitors: int
    total_responses: int
    user_brand_mention_rate: float
    top_competitor_mention_rate: float
    last_analysis_date: Optional[datetime] = None

class CompetitorComparison(BaseModel):
    competitor_name: str
    user_mentions: int
    competitor_mentions: int
    mention_ratio: float
    trend: str  # "up", "down", "stable"

class ModelPerformance(BaseModel):
    provider: LLMProvider
    model: str
    total_responses: int
    user_brand_mentions: int
    mention_rate: float
    avg_response_time: Optional[float] = None 