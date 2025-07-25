-- Geo Analytics Database Schema for Supabase
-- This file contains the complete database schema for the Geo Analytics application

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    website TEXT NOT NULL,
    sector VARCHAR(255) NOT NULL,
    business_size VARCHAR(50) CHECK (business_size IN ('startup', 'small', 'medium', 'large', 'enterprise')),
    location VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Competitors table
CREATE TABLE competitors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    website TEXT,
    description TEXT,
    is_auto_discovered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prompts table
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_auto_generated BOOLEAN DEFAULT FALSE,
    category VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API configurations table (stores user's LLM preferences, not API keys)
CREATE TABLE api_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) CHECK (provider IN ('openai', 'anthropic', 'gemini')),
    model VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- LLM responses table
CREATE TABLE llm_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    provider VARCHAR(50) CHECK (provider IN ('openai', 'anthropic', 'gemini')),
    model VARCHAR(100) NOT NULL,
    response_content TEXT NOT NULL,
    response_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics results table
CREATE TABLE analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    llm_response_id UUID NOT NULL REFERENCES llm_responses(id) ON DELETE CASCADE,
    user_brand_mentions INTEGER DEFAULT 0,
    competitor_mentions JSONB DEFAULT '{}',
    total_mentions INTEGER DEFAULT 0,
    mention_details JSONB DEFAULT '[]',
    analysis_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bulk test tracking table
CREATE TABLE bulk_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) CHECK (status IN ('pending', 'running', 'completed', 'failed')) DEFAULT 'pending',
    total_tests INTEGER NOT NULL,
    completed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    estimated_completion TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_competitors_user_id ON competitors(user_id);
CREATE INDEX idx_prompts_user_id ON prompts(user_id);
CREATE INDEX idx_prompts_category ON prompts(category);
CREATE INDEX idx_api_configurations_user_id ON api_configurations(user_id);
CREATE INDEX idx_llm_responses_user_id ON llm_responses(user_id);
CREATE INDEX idx_llm_responses_prompt_id ON llm_responses(prompt_id);
CREATE INDEX idx_llm_responses_provider_model ON llm_responses(provider, model);
CREATE INDEX idx_analytics_user_id ON analytics(user_id);
CREATE INDEX idx_analytics_prompt_id ON analytics(prompt_id);
CREATE INDEX idx_analytics_llm_response_id ON analytics(llm_response_id);
CREATE INDEX idx_bulk_tests_user_id ON bulk_tests(user_id);
CREATE INDEX idx_bulk_tests_status ON bulk_tests(status);

-- Full-text search indexes
CREATE INDEX idx_llm_responses_content_gin ON llm_responses USING gin(to_tsvector('english', response_content));
CREATE INDEX idx_prompts_content_gin ON prompts USING gin(to_tsvector('english', content));

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitors ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE bulk_tests ENABLE ROW LEVEL SECURITY;

-- RLS Policies (basic examples - you'll need to adapt based on your authentication)
-- These assume you have user authentication set up

-- Users can only access their own data
CREATE POLICY users_select_own ON users FOR SELECT USING (auth.uid()::text = id::text);
CREATE POLICY users_update_own ON users FOR UPDATE USING (auth.uid()::text = id::text);
CREATE POLICY users_insert_own ON users FOR INSERT WITH CHECK (auth.uid()::text = id::text);

-- Competitors policies
CREATE POLICY competitors_select_own ON competitors FOR SELECT USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = competitors.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY competitors_insert_own ON competitors FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM users WHERE users.id = competitors.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY competitors_update_own ON competitors FOR UPDATE USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = competitors.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY competitors_delete_own ON competitors FOR DELETE USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = competitors.user_id AND auth.uid()::text = users.id::text)
);

-- Prompts policies
CREATE POLICY prompts_select_own ON prompts FOR SELECT USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = prompts.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY prompts_insert_own ON prompts FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM users WHERE users.id = prompts.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY prompts_update_own ON prompts FOR UPDATE USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = prompts.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY prompts_delete_own ON prompts FOR DELETE USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = prompts.user_id AND auth.uid()::text = users.id::text)
);

-- API configurations policies
CREATE POLICY api_configurations_select_own ON api_configurations FOR SELECT USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = api_configurations.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY api_configurations_insert_own ON api_configurations FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM users WHERE users.id = api_configurations.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY api_configurations_update_own ON api_configurations FOR UPDATE USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = api_configurations.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY api_configurations_delete_own ON api_configurations FOR DELETE USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = api_configurations.user_id AND auth.uid()::text = users.id::text)
);

-- LLM responses policies
CREATE POLICY llm_responses_select_own ON llm_responses FOR SELECT USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = llm_responses.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY llm_responses_insert_own ON llm_responses FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM users WHERE users.id = llm_responses.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY llm_responses_delete_own ON llm_responses FOR DELETE USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = llm_responses.user_id AND auth.uid()::text = users.id::text)
);

-- Analytics policies
CREATE POLICY analytics_select_own ON analytics FOR SELECT USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = analytics.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY analytics_insert_own ON analytics FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM users WHERE users.id = analytics.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY analytics_delete_own ON analytics FOR DELETE USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = analytics.user_id AND auth.uid()::text = users.id::text)
);

-- Bulk tests policies
CREATE POLICY bulk_tests_select_own ON bulk_tests FOR SELECT USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = bulk_tests.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY bulk_tests_insert_own ON bulk_tests FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM users WHERE users.id = bulk_tests.user_id AND auth.uid()::text = users.id::text)
);
CREATE POLICY bulk_tests_update_own ON bulk_tests FOR UPDATE USING (
    EXISTS (SELECT 1 FROM users WHERE users.id = bulk_tests.user_id AND auth.uid()::text = users.id::text)
);

-- Triggers to automatically update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_competitors_updated_at BEFORE UPDATE ON competitors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_prompts_updated_at BEFORE UPDATE ON prompts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_api_configurations_updated_at BEFORE UPDATE ON api_configurations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bulk_tests_updated_at BEFORE UPDATE ON bulk_tests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE VIEW user_analytics_summary AS
SELECT 
    u.id as user_id,
    u.business_name,
    u.sector,
    u.location,
    COUNT(DISTINCT p.id) as total_prompts,
    COUNT(DISTINCT c.id) as total_competitors,
    COUNT(DISTINCT lr.id) as total_responses,
    COUNT(DISTINCT a.id) as total_analytics,
    COALESCE(AVG(a.user_brand_mentions), 0) as avg_user_mentions,
    COALESCE(AVG(a.total_mentions), 0) as avg_total_mentions,
    MAX(a.created_at) as last_analysis_date
FROM users u
LEFT JOIN prompts p ON u.id = p.user_id
LEFT JOIN competitors c ON u.id = c.user_id
LEFT JOIN llm_responses lr ON u.id = lr.user_id
LEFT JOIN analytics a ON u.id = a.user_id
GROUP BY u.id, u.business_name, u.sector, u.location;

-- Performance monitoring view
CREATE VIEW model_performance_summary AS
SELECT 
    lr.user_id,
    lr.provider,
    lr.model,
    COUNT(*) as total_responses,
    COUNT(DISTINCT lr.prompt_id) as unique_prompts,
    COALESCE(SUM(a.user_brand_mentions), 0) as total_user_mentions,
    COALESCE(AVG(a.user_brand_mentions), 0) as avg_user_mentions_per_response,
    COALESCE(AVG(a.total_mentions), 0) as avg_total_mentions_per_response
FROM llm_responses lr
LEFT JOIN analytics a ON lr.id = a.llm_response_id
GROUP BY lr.user_id, lr.provider, lr.model;

-- Comments for documentation
COMMENT ON TABLE users IS 'Stores user account information and business details';
COMMENT ON TABLE competitors IS 'Stores competitor information for each user';
COMMENT ON TABLE prompts IS 'Stores test prompts for LLM evaluation';
COMMENT ON TABLE api_configurations IS 'Stores user preferences for LLM models (no API keys)';
COMMENT ON TABLE llm_responses IS 'Stores raw responses from LLM APIs';
COMMENT ON TABLE analytics IS 'Stores processed analytics results from LLM responses';
COMMENT ON TABLE bulk_tests IS 'Tracks status of bulk testing operations';

COMMENT ON COLUMN users.business_size IS 'Size category of the business';
COMMENT ON COLUMN competitors.is_auto_discovered IS 'Whether competitor was found automatically via LLM';
COMMENT ON COLUMN prompts.is_auto_generated IS 'Whether prompt was generated automatically';
COMMENT ON COLUMN analytics.competitor_mentions IS 'JSON object mapping competitor names to mention counts';
COMMENT ON COLUMN analytics.mention_details IS 'JSON array of detailed mention information';
COMMENT ON COLUMN analytics.analysis_metadata IS 'Additional analysis data from LLM processing'; 