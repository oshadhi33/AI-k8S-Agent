-- InsForge migration: investigation history table
CREATE TABLE IF NOT EXISTS investigations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    namespace TEXT NOT NULL DEFAULT 'default',
    target_pod TEXT,
    status TEXT NOT NULL DEFAULT 'investigating',
    root_cause TEXT,
    problem_type TEXT,
    confidence INTEGER,
    analysis TEXT,
    suggested_fixes JSONB DEFAULT '[]'::jsonb,
    prevention JSONB DEFAULT '[]'::jsonb,
    affected_resources JSONB DEFAULT '[]'::jsonb,
    evidence_summary JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    user_id UUID REFERENCES auth.users(id)
);

CREATE INDEX IF NOT EXISTS idx_investigations_created_at ON investigations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_investigations_user_id ON investigations(user_id);

-- RLS: users see their own investigations
ALTER TABLE investigations ENABLE ROW LEVEL SECURITY;

CREATE POLICY investigations_select_own ON investigations
    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY investigations_insert_own ON investigations
    FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY investigations_update_own ON investigations
    FOR UPDATE USING (auth.uid() = user_id OR user_id IS NULL);
