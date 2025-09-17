#!/usr/bin/env python3
"""
Stock Photo Manager - Core logic for managing bid card stock photos
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database_simple import get_client
from typing import Optional, Dict, List, Any

class StockPhotoManager:
    """Manages stock photos for bid cards"""
    
    def __init__(self):
        self.supabase = get_client()
    
    def get_stock_photo_for_project_type(self, project_type: str) -> Optional[str]:
        """
        Get stock photo URL for a project type
        Returns None if no stock photo available
        """
        try:
            # Clean the project type string for matching
            project_type_slug = project_type.lower().replace(' ', '_')
            
            # First try exact match
            result = self.supabase.table('project_type_stock_photos').select('photo_url').eq(
                'project_type_slug', project_type_slug
            ).eq('is_active', True).order('priority').limit(1).execute()
            
            if result.data:
                return result.data[0]['photo_url']
            
            # Try partial match on first word (e.g., "kitchen" from "kitchen_remodel")
            first_word = project_type_slug.split('_')[0]
            result = self.supabase.table('project_type_stock_photos').select('photo_url').ilike(
                'project_type_slug', f'%{first_word}%'
            ).eq('is_active', True).order('priority').limit(1).execute()
            
            if result.data:
                return result.data[0]['photo_url']
            
            return None
            
        except Exception as e:
            print(f"Error getting stock photo: {e}")
            return None
    
    def get_bid_card_photo(self, bid_card_id: str) -> Dict[str, Any]:
        """
        Get the appropriate photo for a bid card
        Returns photo URL and source (homeowner/stock/none)
        """
        try:
            # Get bid card data
            result = self.supabase.table('bid_cards').select('*').eq('id', bid_card_id).single().execute()
            
            if not result.data:
                return {'photo_url': None, 'source': 'none'}
            
            bid_card = result.data
            bid_document = bid_card.get('bid_document', {}) or {}
            
            # Check for homeowner photos
            project_images = bid_document.get('project_images', [])
            rfi_photos = bid_document.get('rfi_photos', [])
            
            # Priority 1: Homeowner uploaded photos
            if project_images and len(project_images) > 0:
                # Return first homeowner photo
                photo = project_images[0]
                photo_url = photo.get('url') if isinstance(photo, dict) else photo
                return {
                    'photo_url': photo_url,
                    'source': 'homeowner',
                    'all_photos': project_images
                }
            
            # Priority 2: RFI photos (photos requested and provided)
            if rfi_photos and len(rfi_photos) > 0:
                photo = rfi_photos[0]
                photo_url = photo.get('url') if isinstance(photo, dict) else photo
                return {
                    'photo_url': photo_url,
                    'source': 'homeowner_rfi',
                    'all_photos': rfi_photos
                }
            
            # Priority 3: Stock photo based on project type
            project_type = bid_card.get('project_type', '')
            if project_type:
                stock_photo = self.get_stock_photo_for_project_type(project_type)
                if stock_photo:
                    return {
                        'photo_url': stock_photo,
                        'source': 'stock',
                        'all_photos': [stock_photo]
                    }
            
            # No photo available
            return {'photo_url': None, 'source': 'none', 'all_photos': []}
            
        except Exception as e:
            print(f"Error getting bid card photo: {e}")
            return {'photo_url': None, 'source': 'error'}
    
    def upload_stock_photo(self, project_type_slug: str, photo_url: str, 
                          alt_text: str = None, priority: int = 1) -> bool:
        """Upload a stock photo for a project type"""
        try:
            data = {
                'project_type_slug': project_type_slug.lower().replace(' ', '_'),
                'photo_url': photo_url,
                'alt_text': alt_text or f"Stock photo for {project_type_slug}",
                'priority': priority,
                'is_active': True
            }
            
            result = self.supabase.table('project_type_stock_photos').insert(data).execute()
            return True
            
        except Exception as e:
            print(f"Error uploading stock photo: {e}")
            return False
    
    def bulk_upload_stock_photos(self, photos: List[Dict[str, Any]]) -> Dict[str, int]:
        """Bulk upload stock photos"""
        success_count = 0
        error_count = 0
        
        for photo in photos:
            if self.upload_stock_photo(
                photo.get('project_type_slug'),
                photo.get('photo_url'),
                photo.get('alt_text'),
                photo.get('priority', 1)
            ):
                success_count += 1
                print(f"✅ Uploaded: {photo.get('project_type_slug')}")
            else:
                error_count += 1
                print(f"❌ Failed: {photo.get('project_type_slug')}")
        
        return {
            'success': success_count,
            'errors': error_count,
            'total': len(photos)
        }
    
    def update_bid_card_stock_photo(self, bid_card_id: str) -> bool:
        """
        Force update stock photo for a bid card
        Only sets stock photo if no homeowner photos exist
        """
        try:
            # Get bid card
            result = self.supabase.table('bid_cards').select('*').eq('id', bid_card_id).single().execute()
            if not result.data:
                return False
            
            bid_card = result.data
            bid_document = bid_card.get('bid_document', {}) or {}
            
            # Check if homeowner has photos
            project_images = bid_document.get('project_images', [])
            if project_images and len(project_images) > 0:
                # Has homeowner photos, don't override
                update_data = {
                    'photo_source': 'homeowner',
                    'stock_photo_url': None
                }
            else:
                # No homeowner photos, get stock photo
                project_type = bid_card.get('project_type', '')
                stock_photo = self.get_stock_photo_for_project_type(project_type)
                
                if stock_photo:
                    update_data = {
                        'photo_source': 'stock',
                        'stock_photo_url': stock_photo
                    }
                else:
                    update_data = {
                        'photo_source': 'none',
                        'stock_photo_url': None
                    }
            
            # Update bid card
            self.supabase.table('bid_cards').update(update_data).eq('id', bid_card_id).execute()
            return True
            
        except Exception as e:
            print(f"Error updating bid card stock photo: {e}")
            return False
    
    def get_project_types_without_photos(self) -> List[str]:
        """Get list of project types that don't have stock photos"""
        try:
            # Get all unique project types from bid cards
            bid_cards = self.supabase.table('bid_cards').select('project_type').execute()
            all_project_types = set([b['project_type'] for b in bid_cards.data if b.get('project_type')])
            
            # Get project types with stock photos
            stock_photos = self.supabase.table('project_type_stock_photos').select('project_type_slug').execute()
            types_with_photos = set([s['project_type_slug'] for s in stock_photos.data])
            
            # Find missing ones
            missing = []
            for pt in all_project_types:
                pt_slug = pt.lower().replace(' ', '_')
                if pt_slug not in types_with_photos:
                    missing.append(pt)
            
            return sorted(missing)
            
        except Exception as e:
            print(f"Error getting project types without photos: {e}")
            return []