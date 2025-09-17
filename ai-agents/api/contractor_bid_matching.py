"""
Contractor Bid Card Matching API
Provides personalized bid card matching for contractors based on their profile
"""
import logging
from typing import List, Dict, Any, Optional
from database_simple import SupabaseDB
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContractorProfile:
    """Contractor profile for matching"""
    contractor_id: str
    main_service_type: str
    specialties: List[str]
    zip_codes: List[str] 
    service_radius_miles: int
    contractor_size_category: str
    years_in_business: Optional[int] = None
    certifications: List[str] = None

@dataclass
class MatchingProject:
    """Project that matches contractor profile"""
    id: str
    title: str
    description: str
    budget_range: Dict[str, int]
    location: Dict[str, str]
    project_type: str
    categories: List[str]
    timeline: Dict[str, str]
    match_score: int
    match_reasons: List[str]
    status: str
    urgency_level: str

class ContractorBidMatcher:
    """Handles contractor-specific bid card matching"""
    
    def __init__(self):
        from database_simple import db
        self.client = db.client
        
    def get_matching_projects(self, contractor_profile: ContractorProfile, limit: int = 10) -> List[MatchingProject]:
        """
        Find projects that match contractor profile using existing matching system
        """
        try:
            logger.info(f"Finding matching projects for contractor {contractor_profile.contractor_id}")
            
            # Build matching query based on contractor profile
            query = self.client.table('bid_cards').select("""
                id, bid_card_number, title, description, project_type, 
                urgency_level, status, contractor_count_needed,
                budget_min, budget_max, location_city, location_state, location_zip, 
                location_address, location_lat, location_lng, timeline_start, timeline_end, 
                categories, created_at, bid_document,
                user_id, complexity_score
            """)
            
            # Filter by active bid cards that are still accepting bids
            query = query.in_('status', ['generated', 'active', 'collecting_bids', 'discovery'])
            
            # Execute query
            result = query.limit(limit * 3).execute()  # Get extra to filter and score
            
            if not result.data:
                logger.info("No active bid cards found")
                return []
            
            # Score and filter projects
            matching_projects = []
            for project in result.data:
                match_score, match_reasons = self._calculate_match_score(project, contractor_profile)
                
                # Only include projects with decent match score (>30%)
                if match_score >= 30:
                    matching_project = self._build_matching_project(project, match_score, match_reasons)
                    matching_projects.append(matching_project)
            
            # Sort by match score and return top matches
            matching_projects.sort(key=lambda x: x.match_score, reverse=True)
            return matching_projects[:limit]
            
        except Exception as e:
            logger.error(f"Error finding matching projects: {e}")
            return []
    
    def _calculate_match_score(self, project: Dict[str, Any], contractor: ContractorProfile) -> tuple[int, List[str]]:
        """
        Calculate match score and reasons based on existing matching system
        """
        score = 0
        reasons = []
        
        # Service Type Matching (40% of score)
        project_type = (project.get('project_type') or '').lower()
        categories = project.get('categories', []) or []
        
        # Check main service type
        if contractor.main_service_type and contractor.main_service_type.lower() in project_type:
            score += 25
            reasons.append(f"Specializes in {contractor.main_service_type}")
        
        # Check specialties against categories
        specialty_matches = 0
        for specialty in (contractor.specialties or []):
            for category in categories:
                if specialty and category and (specialty.lower() in category.lower() or category.lower() in specialty.lower()):
                    specialty_matches += 1
                    
        if specialty_matches > 0:
            score += min(15, specialty_matches * 5)
            reasons.append(f"Matches {specialty_matches} project categories")
        
        # Location Matching (30% of score) 
        project_zip = project.get('location_zip')
        project_city = project.get('location_city', 'Unknown')
        project_state = project.get('location_state', 'Unknown')
        
        if project_zip and contractor.zip_codes:
            if project_zip in contractor.zip_codes:
                score += 20
                reasons.append(f"In your service area ({project_city}, {project_state})")
            elif self._is_within_radius({'zip_code': project_zip, 'city': project_city}, contractor):
                score += 15
                reasons.append(f"Within {contractor.service_radius_miles}mi service radius")
        
        # Project Size Matching (20% of score)
        budget_min = project.get('budget_min', 0) or 0
        budget_max = project.get('budget_max', 0) or 0
        
        if budget_min > 0 and budget_max > 0:
            project_size = self._determine_project_size(budget_min, budget_max)
            if self._business_size_matches(contractor.contractor_size_category, project_size):
                score += 15
                reasons.append(f"Perfect fit for {contractor.contractor_size_category.lower().replace('_', ' ')} businesses")
            elif self._business_size_flexible_match(contractor.contractor_size_category, project_size):
                score += 10
                reasons.append("Good fit for your business size")
        
        # Urgency Bonus (10% of score)
        urgency = (project.get('urgency_level') or '').lower()
        if urgency in ['emergency', 'urgent']:
            score += 10
            reasons.append("Urgent project - fast response needed")
        
        # Experience Matching Bonus
        if contractor.years_in_business and contractor.years_in_business >= 5:
            complexity = project.get('complexity_score', 0) or 0
            if complexity >= 7:  # High complexity projects
                score += 5
                reasons.append("Complex project matching your experience level")
        
        return min(100, score), reasons
    
    def _determine_project_size(self, budget_min: int, budget_max: int) -> str:
        """Determine project size category based on budget"""
        avg_budget = (budget_min + budget_max) / 2
        
        if avg_budget < 1000:
            return 'solo_handyman'
        elif avg_budget < 10000:
            return 'owner_operator'
        elif avg_budget < 50000:
            return 'small_business'
        else:
            return 'regional_company'
    
    def _business_size_matches(self, contractor_size: str, project_size: str) -> bool:
        """Check exact business size match"""
        return contractor_size == project_size
    
    def _business_size_flexible_match(self, contractor_size: str, project_size: str) -> bool:
        """Check ±1 tier business size match (from existing matching system)"""
        size_tiers = [
            'solo_handyman',
            'owner_operator', 
            'small_business',
            'regional_company'
        ]
        
        try:
            contractor_idx = size_tiers.index(contractor_size)
            project_idx = size_tiers.index(project_size)
            return abs(contractor_idx - project_idx) <= 1
        except ValueError:
            return False
    
    def _is_within_radius(self, project_location: Dict, contractor: ContractorProfile) -> bool:
        """Check if project is within contractor's service radius"""
        # Simplified radius check - would use PostGIS in production
        # For now, assume within radius if in nearby ZIP codes
        project_zip = project_location.get('zip_code', '')
        if not project_zip:
            return False
            
        # Simple heuristic: if ZIP codes are numerically close, assume within radius
        for contractor_zip in contractor.zip_codes:
            try:
                if abs(int(project_zip) - int(contractor_zip)) <= 50:  # Rough ZIP proximity
                    return True
            except (ValueError, TypeError):
                continue
        return False
    
    def _build_matching_project(self, project: Dict[str, Any], match_score: int, match_reasons: List[str]) -> MatchingProject:
        """Build MatchingProject from database result"""
        return MatchingProject(
            id=project['id'],
            title=project.get('title', 'Home Improvement Project'),
            description=project.get('description', ''),
            budget_range={
                'min': project.get('budget_min', 0) or 0,
                'max': project.get('budget_max', 0) or 0
            },
            location={
                'city': project.get('location_city', 'Unknown'),
                'state': project.get('location_state', 'Unknown'),
                'zip_code': project.get('location_zip', '')
            },
            project_type=project.get('project_type', 'Home Improvement'),
            categories=project.get('categories', []) or [],
            timeline={
                'start_date': project.get('timeline_start', ''),
                'end_date': project.get('timeline_end', ''),
            },
            match_score=match_score,
            match_reasons=match_reasons,
            status=project.get('status', 'active'),
            urgency_level=project.get('urgency_level', 'standard')
        )

# API Functions for FastAPI integration
async def find_matching_projects(contractor_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    API endpoint to find matching projects for a contractor
    """
    try:
        # Parse contractor profile from request
        contractor_profile = ContractorProfile(
            contractor_id=contractor_request.get('contractor_id', ''),
            main_service_type=contractor_request.get('main_service_type', ''),
            specialties=contractor_request.get('specialties', []),
            zip_codes=contractor_request.get('zip_codes', []),
            service_radius_miles=contractor_request.get('service_radius_miles', 25),
            contractor_size_category=contractor_request.get('contractor_size_category', 'small_business'),
            years_in_business=contractor_request.get('years_in_business'),
            certifications=contractor_request.get('certifications', [])
        )
        
        # Find matching projects
        matcher = ContractorBidMatcher()
        matching_projects = matcher.get_matching_projects(contractor_profile, limit=10)
        
        # Convert to dict for JSON response
        projects_data = []
        for project in matching_projects:
            projects_data.append({
                'id': project.id,
                'title': project.title,
                'description': project.description,
                'budget_range': project.budget_range,
                'location': project.location,
                'project_type': project.project_type,
                'categories': project.categories,
                'timeline': project.timeline,
                'match_score': project.match_score,
                'match_reasons': project.match_reasons,
                'status': project.status,
                'urgency_level': project.urgency_level
            })
        
        logger.info(f"Found {len(matching_projects)} matching projects for contractor {contractor_profile.contractor_id}")
        
        return {
            'success': True,
            'contractor_id': contractor_profile.contractor_id,
            'matching_projects': projects_data,
            'total_matches': len(projects_data)
        }
        
    except Exception as e:
        logger.error(f"Error in find_matching_projects: {e}")
        return {
            'success': False,
            'error': str(e),
            'matching_projects': [],
            'total_matches': 0
        }