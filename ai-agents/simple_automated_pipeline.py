#!/usr/bin/env python3
"""
SIMPLE AUTOMATED PIPELINE
Monitors bid cards and enriches existing contractors
"""
import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add parent directory for imports
sys.path.append(os.path.dirname(__file__))
from database_simple import get_client

# Load environment
load_dotenv(override=True)


class SimpleAutomatedPipeline:
    """
    Simplified pipeline that:
    1. Monitors for bid cards with discovered contractors
    2. Enriches contractors that need it
    3. Creates campaigns when ready
    """
    
    def __init__(self):
        self.supabase = get_client()
        
    async def check_for_bid_cards_needing_campaigns(self) -> list:
        """Find bid cards that have contractors but no campaigns"""
        
        # Get bid cards without campaigns
        result = self.supabase.table("bid_cards").select("*").in_(
            "status", ["generated", "approved", "collecting_bids"]
        ).order("created_at", desc=True).limit(10).execute()
        
        bid_cards = []
        for bid_card in result.data:
            # Check if campaign exists
            campaign_check = self.supabase.table("outreach_campaigns").select("id").eq(
                "bid_card_id", bid_card["id"]
            ).execute()
            
            if not campaign_check.data:
                # Check if contractors exist
                contractor_check = self.supabase.table("potential_contractors").select("id").eq(
                    "bid_card_id", bid_card["id"]
                ).execute()
                
                if contractor_check.data:
                    bid_card["contractor_count"] = len(contractor_check.data)
                    bid_cards.append(bid_card)
        
        return bid_cards
    
    async def enrich_contractors_for_bid_card(self, bid_card_id: str) -> int:
        """Enrich contractors that need it"""
        
        print(f"\n[ENRICHMENT] Processing contractors for bid card {bid_card_id}")
        
        # Get contractors needing enrichment
        result = self.supabase.table("potential_contractors").select("*").eq(
            "bid_card_id", bid_card_id
        ).is_("ai_business_summary", None).execute()
        
        contractors = result.data if result.data else []
        
        if not contractors:
            print("  [INFO] All contractors already enriched")
            return 0
        
        print(f"  [FOUND] {len(contractors)} contractors need enrichment")
        
        enriched = 0
        for contractor in contractors:
            # Simple enrichment based on existing data
            review_count = contractor.get('google_review_count', 0) or 0
            
            # Determine size
            if review_count > 500:
                size = 'national_chain'
            elif review_count > 100:
                size = 'regional_company'  
            elif review_count > 20:
                size = 'small_business'
            elif review_count > 5:
                size = 'owner_operator'
            else:
                size = 'solo_handyman'
            
            # Generate summaries
            summary = f"{contractor['company_name']} is a {size.replace('_', ' ')} providing {contractor.get('project_type', 'services')} in {contractor.get('city', 'the area')}. {review_count} reviews, {contractor.get('google_rating', 0)} stars."
            
            capabilities = f"Specializes in {contractor.get('project_type', 'general contracting')} with {review_count} customer reviews."
            
            # Update contractor
            update_result = self.supabase.table('potential_contractors').update({
                'contractor_size_category': size,
                'ai_business_summary': summary,
                'ai_capability_description': capabilities,
                'updated_at': datetime.now().isoformat()
            }).eq('id', contractor['id']).execute()
            
            if update_result.data:
                enriched += 1
                print(f"    ✓ {contractor['company_name']}: {size}")
        
        print(f"  [COMPLETE] Enriched {enriched} contractors")
        return enriched
    
    async def create_campaign_for_bid_card(self, bid_card: Dict[str, Any]) -> bool:
        """Create campaign for bid card with contractors"""
        
        print(f"\n[CAMPAIGN] Creating campaign for {bid_card.get('bid_card_number')}")
        
        try:
            # Get contractor count
            contractors = self.supabase.table("potential_contractors").select("id").eq(
                "bid_card_id", bid_card["id"]
            ).execute()
            
            contractor_count = len(contractors.data) if contractors.data else 0
            
            # Create campaign with correct schema
            campaign_data = {
                "bid_card_id": bid_card["id"],
                "name": f"{bid_card.get('project_type', 'project')} - automated ({contractor_count} contractors)",
                "status": "active",
                "max_contractors": contractor_count,
                "contractors_targeted": contractor_count,
                "messages_sent": 0,
                "responses_received": 0,
                "hot_leads_generated": 0,
                "scheduled_start": datetime.now().isoformat(),
                "actual_start": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table("outreach_campaigns").insert(campaign_data).execute()
            
            if result.data:
                print(f"  [SUCCESS] Campaign created for {contractor_count} contractors")
                
                # Update bid card status
                self.supabase.table("bid_cards").update({
                    "status": "collecting_bids",
                    "updated_at": datetime.now().isoformat()
                }).eq("id", bid_card["id"]).execute()
                
                return True
                
        except Exception as e:
            print(f"  [ERROR] Campaign creation failed: {e}")
        
        return False
    
    async def run_pipeline_cycle(self):
        """Run one complete pipeline cycle"""
        
        print("\n" + "="*80)
        print("AUTOMATED PIPELINE CYCLE")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Step 1: Find bid cards needing campaigns
        bid_cards = await self.check_for_bid_cards_needing_campaigns()
        
        if not bid_cards:
            print("\n[INFO] No bid cards need processing")
            return 0
        
        print(f"\n[FOUND] {len(bid_cards)} bid cards with contractors but no campaigns")
        for bc in bid_cards:
            print(f"  - {bc['bid_card_number']}: {bc['contractor_count']} contractors")
        
        processed = 0
        
        for bid_card in bid_cards:
            print(f"\n{'='*60}")
            print(f"Processing: {bid_card.get('bid_card_number')}")
            print(f"{'='*60}")
            
            try:
                # Step 2: Enrich contractors
                enriched = await self.enrich_contractors_for_bid_card(bid_card["id"])
                
                # Step 3: Create campaign
                campaign_created = await self.create_campaign_for_bid_card(bid_card)
                
                if campaign_created:
                    processed += 1
                    print(f"\n[COMPLETE] Successfully processed bid card")
                    
            except Exception as e:
                print(f"\n[ERROR] Failed to process bid card: {e}")
        
        print("\n" + "="*80)
        print("PIPELINE SUMMARY")
        print(f"  Bid cards found: {len(bid_cards)}")
        print(f"  Successfully processed: {processed}")
        print(f"  Failed: {len(bid_cards) - processed}")
        print("="*80)
        
        return processed
    
    async def run_continuous(self, interval_seconds: int = 300):
        """Run pipeline continuously"""
        
        print("\n" + "="*80)
        print("CONTINUOUS AUTOMATED PIPELINE STARTED")
        print(f"Checking every {interval_seconds} seconds")
        print("Press Ctrl+C to stop")
        print("="*80)
        
        while True:
            try:
                await self.run_pipeline_cycle()
                print(f"\n[WAITING] Next cycle in {interval_seconds} seconds...")
                await asyncio.sleep(interval_seconds)
            except KeyboardInterrupt:
                print("\n[STOPPED] Pipeline stopped by user")
                break
            except Exception as e:
                print(f"\n[ERROR] Cycle failed: {e}")
                print(f"[RETRY] Retrying in {interval_seconds} seconds...")
                await asyncio.sleep(interval_seconds)


async def main():
    """Main entry point"""
    
    pipeline = SimpleAutomatedPipeline()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        await pipeline.run_continuous(interval_seconds=300)
    else:
        # Run once
        processed = await pipeline.run_pipeline_cycle()
        
        if processed == 0:
            print("\n[INFO] No bid cards were processed. The system is up to date.")
        else:
            print(f"\n[SUCCESS] Processed {processed} bid cards successfully!")


if __name__ == "__main__":
    print("""
==================================================================
     INSTABIDS SIMPLE AUTOMATED PIPELINE
==================================================================
 This pipeline:
 1. Finds bid cards with contractors but no campaigns
 2. Enriches contractors with business data
 3. Creates outreach campaigns
 4. Updates bid card status
==================================================================
    """)
    
    asyncio.run(main())