# Agent 4 Contractor Image Management System
**Last Updated**: January 31, 2025  
**Status**: ARCHITECTURE DESIGNED ✅

## Executive Summary

Agent 4 needs a comprehensive **contractor-only** visual portfolio system with dedicated storage buckets and automated image collection. This is separate from the homeowner inspiration system and focuses purely on contractor work showcase and project history.

## Contractor Image Categories ✅

### 1. **Portfolio Images** (Previous Work - External)
- **Source**: Scraped from contractor websites, Google Business profiles
- **Purpose**: Historical work samples from before InstaBids
- **AI Usage**: Help match contractors to similar project types
- **Storage**: `contractor-portfolios/{contractor_id}/`

### 2. **Uploaded Work Samples** (Manual Contractor Uploads)
- **Source**: Contractors manually upload their best work
- **Purpose**: Showcase capabilities to homeowners
- **AI Usage**: Project matching and quality assessment
- **Storage**: `contractor-uploads/{contractor_id}/`

### 3. **InstaBids Project Gallery** (Completed InstaBids Work)
- **Source**: Homeowner uploads + contractor uploads of finished InstaBids projects
- **Purpose**: Platform-verified work history and quality tracking
- **AI Usage**: Contractor performance evaluation
- **Storage**: `instabids-completed/{contractor_id}/`

## Database Schema Design ✅

### New Tables Needed:

#### contractor_images
```sql
CREATE TABLE contractor_images (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    contractor_id uuid NOT NULL REFERENCES contractors(id),
    
    -- Image details
    image_url text NOT NULL,
    thumbnail_url text,
    storage_path text NOT NULL,
    
    -- Categorization
    category varchar NOT NULL CHECK (category IN ('portfolio', 'uploaded', 'instabids_completed')),
    project_type varchar, -- 'kitchen', 'bathroom', 'lawn', etc.
    
    -- Source tracking
    source varchar, -- 'website_scrape', 'google_business', 'manual_upload', 'homeowner_upload'
    source_url text,
    scraped_from_url text,
    
    -- Project association
    bid_card_id uuid REFERENCES bid_cards(id), -- For InstaBids completed work
    project_completion_date date,
    
    -- AI Analysis
    ai_analysis jsonb, -- AI-generated tags, quality scores, project type detection
    tags text[],
    quality_score integer CHECK (quality_score >= 1 AND quality_score <= 10),
    
    -- Display and ordering
    is_featured boolean DEFAULT false,
    display_order integer,
    is_public boolean DEFAULT true,
    
    -- Metadata
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
```

#### contractor_image_collections
```sql
CREATE TABLE contractor_image_collections (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    contractor_id uuid NOT NULL REFERENCES contractors(id),
    
    -- Collection details
    name varchar NOT NULL, -- "Kitchen Remodels", "Bathroom Projects", etc.
    description text,
    collection_type varchar NOT NULL, -- 'project_type', 'time_period', 'featured', 'before_after'
    
    -- Display
    cover_image_id uuid REFERENCES contractor_images(id),
    is_public boolean DEFAULT true,
    display_order integer,
    
    -- Metadata
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
```

#### contractor_image_collection_items
```sql
CREATE TABLE contractor_image_collection_items (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id uuid NOT NULL REFERENCES contractor_image_collections(id),
    image_id uuid NOT NULL REFERENCES contractor_images(id),
    display_order integer,
    created_at timestamptz DEFAULT now(),
    
    UNIQUE(collection_id, image_id)
);
```

## Supabase Storage Bucket Structure ✅

### Bucket Organization:
```
contractor-media/
├── portfolios/
│   └── {contractor_id}/
│       ├── website-scrapes/
│       │   ├── original_001.jpg
│       │   ├── original_002.jpg
│       │   └── thumbnails/
│       └── google-business/
│           ├── review_photo_001.jpg
│           └── thumbnails/
├── uploads/
│   └── {contractor_id}/
│       ├── manual-uploads/
│       │   ├── kitchen_project_001.jpg
│       │   └── bathroom_remodel_003.jpg
│       └── thumbnails/
└── instabids-completed/
    └── {contractor_id}/
        ├── {bid_card_id}/
        │   ├── final_001.jpg
        │   ├── final_002.jpg
        │   └── thumbnails/
        └── before-after-sets/
```

## Automated Image Collection System ✅

### Integration with Profile Enrichment:
```python
# Enhanced CoIA agent with image collection
class CoIAImageCollector:
    async def collect_contractor_images(self, contractor_id: str, contractor_data: dict):
        """Collect images from multiple sources automatically"""
        
        images_collected = []
        
        # 1. Website scraping (integrate with existing PlaywrightWebsiteEnricher)
        if contractor_data.get('website'):
            website_images = await self.scrape_website_images(
                contractor_data['website'], 
                contractor_id
            )
            images_collected.extend(website_images)
        
        # 2. Google Business Profile images
        if contractor_data.get('google_business_url'):
            google_images = await self.collect_google_business_images(
                contractor_data['google_business_url'],
                contractor_id
            )
            images_collected.extend(google_images)
        
        # 3. Social media scraping (future enhancement)
        # Instagram, Facebook business pages, etc.
        
        # 4. Store images and create database records
        for image_data in images_collected:
            await self.store_contractor_image(contractor_id, image_data)
        
        return len(images_collected)
```

### Website Image Scraping:
```python
async def scrape_website_images(self, website_url: str, contractor_id: str):
    """Enhanced website scraper to collect portfolio images"""
    
    # Use existing Playwright tools
    await self.playwright_client.navigate(website_url)
    
    # Look for gallery/portfolio sections
    gallery_selectors = [
        'img[src*="gallery"]',
        'img[src*="portfolio"]', 
        'img[src*="project"]',
        '.gallery img',
        '.portfolio img',
        '[data-lightbox] img'
    ]
    
    images_found = []
    for selector in gallery_selectors:
        elements = await self.playwright_client.query_all(selector)
        for img in elements:
            src = await img.get_attribute('src')
            alt = await img.get_attribute('alt')
            
            # Download and analyze image
            image_data = await self.download_and_analyze_image(src, {
                'source': 'website_scrape',
                'source_url': website_url,
                'alt_text': alt,
                'contractor_id': contractor_id,
                'category': 'portfolio'
            })
            
            if image_data:
                images_found.append(image_data)
    
    return images_found
```

## AI-Powered Image Analysis ✅

### Image Classification and Matching:
```python
class ContractorImageAnalyzer:
    """AI analysis for contractor images"""
    
    async def analyze_contractor_image(self, image_url: str, contractor_data: dict):
        """Analyze image for project type, quality, and matching"""
        
        # Use Claude Vision or OpenAI Vision
        analysis_prompt = f"""
        Analyze this contractor work image for:
        1. Project type (kitchen, bathroom, lawn, roofing, etc.)
        2. Quality score (1-10)
        3. Style/materials visible
        4. Completion stage (before, during, after)
        5. Key features for project matching
        
        Contractor specializes in: {contractor_data.get('specialties', [])}
        """
        
        vision_response = await self.vision_client.analyze_image(image_url, analysis_prompt)
        
        return {
            'project_type': vision_response.get('project_type'),
            'quality_score': vision_response.get('quality_score'),
            'materials': vision_response.get('materials', []),
            'style': vision_response.get('style'),
            'completion_stage': vision_response.get('completion_stage'),
            'ai_tags': vision_response.get('generated_tags', []),
            'suitability_score': self.calculate_project_match_score(
                vision_response, 
                contractor_data
            )
        }
```

## Frontend Integration ✅

### Contractor Image Management Interface:
```typescript
// ContractorImageGallery.tsx
interface ContractorImageGalleryProps {
    contractorId: string;
    editable?: boolean;
}

export function ContractorImageGallery({ contractorId, editable }: ContractorImageGalleryProps) {
    const [images, setImages] = useState<ContractorImage[]>([]);
    const [collections, setCollections] = useState<ImageCollection[]>([]);
    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    
    return (
        <div className="contractor-image-gallery">
            {/* Category filters */}
            <div className="image-categories">
                <button onClick={() => setSelectedCategory('portfolio')}>
                    Portfolio ({getImageCount('portfolio')})
                </button>
                <button onClick={() => setSelectedCategory('uploaded')}>
                    My Uploads ({getImageCount('uploaded')})
                </button>
                <button onClick={() => setSelectedCategory('instabids_completed')}>
                    InstaBids Projects ({getImageCount('instabids_completed')})
                </button>
            </div>
            
            {/* Image upload area */}
            {editable && (
                <ImageUploadZone 
                    contractorId={contractorId}
                    onUpload={handleImageUpload}
                />
            )}
            
            {/* Image grid with AI-powered organization */}
            <div className="image-grid">
                {filteredImages.map(image => (
                    <ContractorImageCard 
                        key={image.id}
                        image={image}
                        showProjectType={true}
                        showQualityScore={editable}
                        onEdit={editable ? handleEditImage : undefined}
                    />
                ))}
            </div>
            
            {/* Featured collections */}
            <div className="featured-collections">
                {collections.map(collection => (
                    <ImageCollectionCard 
                        key={collection.id}
                        collection={collection}
                        images={getCollectionImages(collection.id)}
                    />
                ))}
            </div>
        </div>
    );
}
```

## API Endpoints ✅

### Contractor Image Management:
```python
# New API endpoints for Agent 4
@app.get("/api/contractors/{contractor_id}/images")
async def get_contractor_images(contractor_id: str, category: str = None):
    """Get all images for a contractor, optionally filtered by category"""

@app.post("/api/contractors/{contractor_id}/images/upload")
async def upload_contractor_image(contractor_id: str, file: UploadFile):
    """Upload new image to contractor's gallery"""

@app.post("/api/contractors/{contractor_id}/images/collect")
async def trigger_image_collection(contractor_id: str):
    """Trigger automated image collection from web sources"""

@app.put("/api/contractors/images/{image_id}")
async def update_image_metadata(image_id: str, metadata: dict):
    """Update image tags, category, or other metadata"""

@app.post("/api/contractors/{contractor_id}/collections")
async def create_image_collection(contractor_id: str, collection_data: dict):
    """Create new image collection (portfolio grouping)"""
```

## AI-Powered Project Matching ✅

### How Images Help Project Matching:
```python
class ProjectContractorMatcher:
    """Enhanced project matching using contractor images"""
    
    async def find_suitable_contractors(self, bid_card: dict):
        """Find contractors based on project requirements + image portfolio"""
        
        project_type = bid_card['project_type']
        project_style = bid_card.get('style_preferences')
        project_scope = bid_card.get('scope')
        
        # Query contractors with relevant portfolio images
        query = """
        SELECT DISTINCT c.*, 
               COUNT(ci.id) as relevant_image_count,
               AVG(ci.quality_score) as avg_quality_score
        FROM contractors c
        JOIN contractor_images ci ON c.id = ci.contractor_id
        WHERE ci.project_type = %s
        AND ci.quality_score >= 7
        AND c.specialties @> %s
        GROUP BY c.id
        ORDER BY relevant_image_count DESC, avg_quality_score DESC
        """
        
        return await self.db.execute(query, [project_type, [project_type]])
```

## Implementation Priority ✅

### Phase 1: Core Infrastructure (2 hours)
1. Create database tables for contractor images
2. Set up Supabase storage buckets with proper policies
3. Basic image upload API endpoints

### Phase 2: Automated Collection (3 hours) 
1. Integrate image scraping with existing PlaywrightWebsiteEnricher
2. Google Business Profile image collection
3. AI image analysis and categorization

### Phase 3: Frontend Gallery (2 hours)
1. Contractor image gallery component
2. Upload interface and image management
3. Collection creation and organization

### Phase 4: Project Matching (1 hour)
1. Enhanced contractor matching using image portfolio
2. Quality scoring and contractor ranking
3. Analytics on image performance

## Success Metrics ✅

### Technical Performance:
- Image collection success rate >80% from contractor websites
- AI analysis accuracy >85% for project type detection
- Image storage and retrieval latency <2 seconds
- Upload success rate >95%

### Business Impact:
- Contractor profile visual completeness >70% 
- Project-contractor match accuracy improvement >15%
- Homeowner engagement with contractor profiles >60%
- Contractor portfolio update frequency >1x/month

**This system positions Agent 4 as the complete visual contractor management platform, separate from homeowner inspiration boards, focused purely on contractor work showcase and performance tracking.**