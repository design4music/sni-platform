-- Add 'blocked_llm' to processing_status check constraint

BEGIN;

-- Drop old constraint
ALTER TABLE titles_v3
DROP CONSTRAINT IF EXISTS titles_v3_processing_status_check;

-- Add new constraint with 'blocked_llm'
ALTER TABLE titles_v3
ADD CONSTRAINT titles_v3_processing_status_check
CHECK (processing_status = ANY (ARRAY[
    'pending'::text,
    'assigned'::text,
    'out_of_scope'::text,
    'blocked_stopword'::text,
    'blocked_llm'::text
]));

COMMIT;
