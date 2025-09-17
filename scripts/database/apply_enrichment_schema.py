#!/usr/bin/env python3
"""
Apply database schema changes for contractor enrichment
"""
import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')

if not supabase_url or not supabase_key:
    print("Error: Missing Supabase credentials in .env file")
    sys.exit(1)

client = create_client(supabase_url, supabase_key)

# Schema changes to apply
schema_changes = [
    {
        'name': 'business_size',
        'query': '''
        ALTER TABLE potential_contractors 
        ADD COLUMN IF NOT EXISTS business_size VARCHAR(50)
        ''',
        'description': 'Business size classification'
    },
    {
        'name': 'service_types',
        'query': '''
        ALTER TABLE potential_contractors 
        ADD COLUMN IF NOT EXISTS service_types TEXT[]
        ''',
        'description': 'Array of service types offered'
    },
    {
        'name': 'service_description',
        'query': '''
        ALTER TABLE potential_contractors 
        ADD COLUMN IF NOT EXISTS service_description TEXT
        ''',
        'description': 'Searchable service description'
    },
    {
        'name': 'service_areas',
        'query': '''
        ALTER TABLE potential_contractors 
        ADD COLUMN IF NOT EXISTS service_areas TEXT[]
        ''',
        'description': 'Array of zip codes served'
    },
    {
        'name': 'enrichment_status',
        'query': '''
        ALTER TABLE potential_contractors 
        ADD COLUMN IF NOT EXISTS enrichment_status VARCHAR(50)
        ''',
        'description': 'Status of enrichment process'
    },
    {
        'name': 'enrichment_data',
        'query': '''
        ALTER TABLE potential_contractors 
        ADD COLUMN IF NOT EXISTS enrichment_data JSONB
        ''',
        'description': 'Additional enrichment data in JSON format'
    }
]

print("APPLYING ENRICHMENT SCHEMA CHANGES")
print("=" * 80)

# Apply each change
for change in schema_changes:
    print(f"\nApplying: {change['name']}")
    print(f"Description: {change['description']}")
    
    try:
        # Note: Supabase doesn't have a direct exec_sql method
        # You would need to run these via the Supabase dashboard SQL editor
        # or use a direct PostgreSQL connection
        print(f"SQL: {change['query'].strip()}")
        print("✓ Ready to apply via Supabase SQL editor")
        
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("SCHEMA CHANGES TO APPLY IN SUPABASE SQL EDITOR:")
print("=" * 80)

# Print all SQL for easy copy-paste
full_sql = """
-- Contractor Enrichment Schema Updates

-- 1. Business size classification
ALTER TABLE potential_contractors 
ADD COLUMN IF NOT EXISTS business_size VARCHAR(50);
COMMENT ON COLUMN potential_contractors.business_size IS 'Business size: INDIVIDUAL_HANDYMAN, OWNER_OPERATOR, LOCAL_BUSINESS_TEAMS, NATIONAL_COMPANY';

-- 2. Service types array
ALTER TABLE potential_contractors 
ADD COLUMN IF NOT EXISTS service_types TEXT[];
COMMENT ON COLUMN potential_contractors.service_types IS 'Service types: REPAIR, INSTALLATION, MAINTENANCE, EMERGENCY, CONSULTATION';

-- 3. Searchable service description
ALTER TABLE potential_contractors 
ADD COLUMN IF NOT EXISTS service_description TEXT;
COMMENT ON COLUMN potential_contractors.service_description IS 'Detailed searchable description of services offered';

-- 4. Service areas (zip codes)
ALTER TABLE potential_contractors 
ADD COLUMN IF NOT EXISTS service_areas TEXT[];
COMMENT ON COLUMN potential_contractors.service_areas IS 'Array of zip codes where contractor provides service';

-- 5. Enrichment status
ALTER TABLE potential_contractors 
ADD COLUMN IF NOT EXISTS enrichment_status VARCHAR(50);
COMMENT ON COLUMN potential_contractors.enrichment_status IS 'Status: PENDING, ENRICHED, FAILED, NO_WEBSITE';

-- 6. Additional enrichment data
ALTER TABLE potential_contractors 
ADD COLUMN IF NOT EXISTS enrichment_data JSONB;
COMMENT ON COLUMN potential_contractors.enrichment_data IS 'Additional data from website enrichment';

-- Create indexes for efficient searching
CREATE INDEX IF NOT EXISTS idx_contractors_business_size ON potential_contractors(business_size);
CREATE INDEX IF NOT EXISTS idx_contractors_service_types ON potential_contractors USING GIN(service_types);
CREATE INDEX IF NOT EXISTS idx_contractors_service_areas ON potential_contractors USING GIN(service_areas);
CREATE INDEX IF NOT EXISTS idx_contractors_enrichment_status ON potential_contractors(enrichment_status);

-- Full text search index on service description
CREATE INDEX IF NOT EXISTS idx_contractors_service_description 
ON potential_contractors USING GIN(to_tsvector('english', COALESCE(service_description, '')));
"""

print(full_sql)

print("\n" + "=" * 80)
print("EXAMPLE QUERIES AFTER SCHEMA UPDATE:")
print("=" * 80)

example_queries = """
-- Find LOCAL_BUSINESS_TEAMS lawn care contractors in 33442
SELECT * FROM potential_contractors
WHERE project_type = 'lawn care'
  AND business_size = 'LOCAL_BUSINESS_TEAMS'
  AND '33442' = ANY(service_areas)
ORDER BY google_rating DESC;

-- Find contractors offering REPAIR services
SELECT * FROM potential_contractors
WHERE 'REPAIR' = ANY(service_types)
  AND project_zip_code = '33442';

-- Full text search for sprinkler repair
SELECT * FROM potential_contractors
WHERE to_tsvector('english', service_description) @@ to_tsquery('english', 'sprinkler & repair')
  AND project_type = 'lawn care';

-- Get enrichment statistics
SELECT 
  enrichment_status,
  COUNT(*) as count,
  AVG(CASE WHEN email IS NOT NULL THEN 1 ELSE 0 END) * 100 as email_percentage
FROM potential_contractors
GROUP BY enrichment_status;
"""

print(example_queries)

print("\nTo apply these changes:")
print("1. Go to your Supabase dashboard")
print("2. Navigate to SQL Editor")
print("3. Copy and paste the SQL above")
print("4. Execute the queries")
print("\nThis will add all necessary columns and indexes for the enrichment system.")