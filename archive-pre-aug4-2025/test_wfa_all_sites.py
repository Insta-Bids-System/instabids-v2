"""
Test WFA on All Test Contractor Sites
Comprehensive testing of Website Form Automation across different form types
"""
import json
import os
import time
import uuid
from datetime import datetime

from dotenv import load_dotenv
from supabase import create_client

from agents.wfa.agent import WebsiteFormAutomationAgent


load_dotenv()

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key)


class WFAComprehensiveTester:
    """Test WFA across all test contractor websites"""

    def __init__(self):
        self.wfa = WebsiteFormAutomationAgent()
        self.test_sites = [
            {
                "name": "Simple Contact Form",
                "url": "http://localhost:8008",
                "type": "simple",
                "expected_fields": ["name", "email", "phone", "message"],
                "complexity": "low"
            },
            {
                "name": "Multi-Step Wizard",
                "url": "http://localhost:8008",
                "type": "multi_step",
                "expected_fields": ["company", "name", "email", "phone", "project_type", "message"],
                "complexity": "medium"
            },
            {
                "name": "Enterprise Form with Validation",
                "url": "http://localhost:8008",
                "type": "enterprise",
                "expected_fields": ["company", "name", "email", "phone", "website", "license", "message"],
                "complexity": "high"
            },
            {
                "name": "Modern AJAX Form",
                "url": "http://localhost:8008",
                "type": "ajax",
                "expected_fields": ["name", "email", "phone", "service", "message"],
                "complexity": "medium"
            }
        ]
        self.test_results = []
        self.test_bid_card = None

    def create_test_bid_card(self):
        """Create a test bid card for WFA testing"""
        bid_card_data = {
            "id": f"wfa_test_{uuid.uuid4().hex[:8]}",
            "project_type": "bathroom_remodel",
            "timeline": "Within 2 weeks",
            "urgency": "week",
            "budget_display": "$15,000 - $20,000",
            "budget_range": {"min": 15000, "max": 20000},
            "location": {
                "city": "Tampa",
                "state": "FL",
                "neighborhood": "Hyde Park"
            },
            "project_details": {
                "scope_of_work": [
                    "Replace bathtub with walk-in shower",
                    "Install new vanity and sink",
                    "Update all fixtures",
                    "Retile entire bathroom"
                ],
                "property_details": {
                    "size": "80 sq ft",
                    "year_built": "1995"
                }
            },
            "contractor_count": 3,
            "homeowner_ready": True
        }

        result = supabase.table("bid_cards").insert(bid_card_data).execute()

        if result.data:
            self.test_bid_card = result.data[0]
            print(f"✓ Created test bid card: {self.test_bid_card['id']}")
            return True
        return False

    def create_test_contractor(self, site_info):
        """Create a test contractor for each site"""
        contractor_data = {
            "company_name": f"Test {site_info['name']} Contractor",
            "contact_name": "John Doe",
            "email": f"test_{site_info['type']}@example.com",
            "phone": "555-0123",
            "website": site_info["url"],
            "service_area": ["Tampa", "St. Petersburg"],
            "specialties": ["bathroom_remodel", "kitchen_remodel"],
            "company_size": "5-10",
            "status": "active",
            "test_site_type": site_info["type"]
        }

        result = supabase.table("contractor_leads").insert(contractor_data).execute()

        if result.data:
            return result.data[0]
        return None

    def test_form_analysis(self, contractor, site_info):
        """Test form analysis capabilities"""
        print(f"\n--- Analyzing {site_info['name']} ---")

        start_time = time.time()
        analysis = self.wfa.analyze_website_for_form(contractor)
        analysis_time = time.time() - start_time

        result = {
            "site": site_info["name"],
            "url": site_info["url"],
            "analysis_time": f"{analysis_time:.2f}s",
            "form_found": analysis["has_contact_form"],
            "form_score": analysis.get("form_score", 0),
            "fields_found": len(analysis.get("form_fields", [])),
            "expected_fields": len(site_info["expected_fields"]),
            "submit_method": analysis.get("submit_method", "unknown")
        }

        # Check if all expected fields were found
        if analysis["has_contact_form"]:
            found_fields = [f["name"] for f in analysis.get("form_fields", [])]
            missing_fields = [f for f in site_info["expected_fields"] if f not in found_fields]

            if missing_fields:
                result["missing_fields"] = missing_fields
                print(f"  ⚠️  Missing fields: {', '.join(missing_fields)}")
            else:
                print("  ✓ All expected fields found")

            print(f"  Form score: {analysis.get('form_score', 0)}/100")
            print(f"  Submit method: {analysis.get('submit_method', 'unknown')}")
        else:
            result["error"] = "No form found"
            print("  ✗ No contact form found")

        return result, analysis

    def test_form_filling(self, contractor, site_info, bid_card):
        """Test form filling and submission"""
        print(f"\n--- Filling form on {site_info['name']} ---")

        start_time = time.time()
        fill_result = self.wfa.fill_contact_form(contractor, bid_card)
        fill_time = time.time() - start_time

        result = {
            "site": site_info["name"],
            "fill_time": f"{fill_time:.2f}s",
            "success": fill_result["success"],
            "submission_method": fill_result.get("submission_method"),
            "confidence": fill_result.get("confidence", 0)
        }

        if fill_result["success"]:
            print("  ✓ Form submitted successfully")

            # Verify bid card URL in message
            attempt = supabase.table("contractor_outreach_attempts").select("*").eq(
                "contractor_lead_id", contractor["id"]
            ).order("created_at", desc=True).limit(1).execute()

            if attempt.data:
                message = attempt.data[0].get("message_content", "")
                bid_card_url = f"https://instabids.com/bid-cards/{bid_card['id']}"

                if bid_card_url in message:
                    result["bid_card_url_included"] = True
                    print("  ✓ Bid card URL included in message")
                else:
                    result["bid_card_url_included"] = False
                    print("  ✗ Bid card URL NOT found in message")

                # Extract key message elements
                result["message_preview"] = message[:100] + "..." if len(message) > 100 else message
        else:
            result["error"] = fill_result.get("error", "Unknown error")
            print(f"  ✗ Form submission failed: {result['error']}")

        return result

    def test_special_cases(self):
        """Test special form handling cases"""
        print("\n=== Testing Special Cases ===")

        special_tests = []

        # Test 1: Multi-step form navigation
        if len(self.test_results) > 1 and self.test_results[1]["site"] == "Multi-Step Wizard":
            multi_step_success = self.test_results[1].get("fill_result", {}).get("success", False)
            special_tests.append({
                "test": "Multi-step navigation",
                "passed": multi_step_success,
                "details": "Successfully navigated through form steps" if multi_step_success else "Failed to complete multi-step form"
            })

        # Test 2: Field validation handling
        if len(self.test_results) > 2 and self.test_results[2]["site"] == "Enterprise Form with Validation":
            validation_handled = self.test_results[2].get("fill_result", {}).get("success", False)
            special_tests.append({
                "test": "Validation handling",
                "passed": validation_handled,
                "details": "Passed all field validations" if validation_handled else "Failed validation requirements"
            })

        # Test 3: AJAX form submission
        if len(self.test_results) > 3 and self.test_results[3]["site"] == "Modern AJAX Form":
            ajax_success = self.test_results[3].get("fill_result", {}).get("success", False)
            special_tests.append({
                "test": "AJAX submission",
                "passed": ajax_success,
                "details": "AJAX form submitted successfully" if ajax_success else "AJAX submission failed"
            })

        # Test 4: Message customization with bid card URL
        url_inclusion_rate = sum(
            1 for r in self.test_results
            if r.get("fill_result", {}).get("bid_card_url_included", False)
        ) / len(self.test_results) if self.test_results else 0

        special_tests.append({
            "test": "Bid card URL inclusion",
            "passed": url_inclusion_rate >= 0.8,
            "details": f"{url_inclusion_rate*100:.0f}% of messages included bid card URL"
        })

        return special_tests

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("WFA COMPREHENSIVE TEST REPORT")
        print("=" * 60)

        if self.test_bid_card:
            print(f"\nTest Bid Card: {self.test_bid_card['id']}")
            print(f"Project: {self.test_bid_card['project_type']}")
            print(f"Budget: {self.test_bid_card['budget_display']}")

        print("\nForm Analysis & Submission Results:")
        print("-" * 40)

        total_sites = len(self.test_results)
        successful_submissions = sum(1 for r in self.test_results if r.get("fill_result", {}).get("success", False))

        for result in self.test_results:
            print(f"\n{result['site']}:")

            # Analysis results
            analysis = result.get("analysis_result", {})
            print(f"  Analysis: {'Form found' if analysis.get('form_found') else 'No form found'}")
            if analysis.get("form_found"):
                print(f"    - Score: {analysis.get('form_score')}/100")
                print(f"    - Fields: {analysis.get('fields_found')}/{analysis.get('expected_fields')}")
                print(f"    - Time: {analysis.get('analysis_time')}")

            # Fill results
            fill = result.get("fill_result", {})
            if fill:
                status = "✓ Success" if fill.get("success") else "✗ Failed"
                print(f"  Submission: {status}")
                if fill.get("success"):
                    print(f"    - Method: {fill.get('submission_method')}")
                    print(f"    - Time: {fill.get('fill_time')}")
                    print(f"    - URL included: {'Yes' if fill.get('bid_card_url_included') else 'No'}")
                else:
                    print(f"    - Error: {fill.get('error')}")

        # Special cases
        special_tests = self.test_special_cases()
        if special_tests:
            print("\nSpecial Case Testing:")
            print("-" * 40)
            for test in special_tests:
                status = "✓ PASS" if test["passed"] else "✗ FAIL"
                print(f"{status} {test['test']}: {test['details']}")

        # Summary
        print("\n" + "-" * 40)
        print(f"Overall Success Rate: {successful_submissions}/{total_sites} ({successful_submissions/total_sites*100:.0f}%)")

        # Performance metrics
        avg_analysis_time = sum(
            float(r.get("analysis_result", {}).get("analysis_time", "0s")[:-1])
            for r in self.test_results
        ) / len(self.test_results) if self.test_results else 0

        avg_fill_time = sum(
            float(r.get("fill_result", {}).get("fill_time", "0s")[:-1])
            for r in self.test_results if r.get("fill_result", {}).get("success")
        ) / successful_submissions if successful_submissions > 0 else 0

        print("\nPerformance Metrics:")
        print(f"  Average analysis time: {avg_analysis_time:.2f}s")
        print(f"  Average fill time: {avg_fill_time:.2f}s")

        # Save detailed JSON report
        report_data = {
            "test_date": datetime.utcnow().isoformat(),
            "bid_card_id": self.test_bid_card["id"] if self.test_bid_card else None,
            "summary": {
                "total_sites": total_sites,
                "successful_submissions": successful_submissions,
                "success_rate": f"{successful_submissions/total_sites*100:.0f}%",
                "avg_analysis_time": f"{avg_analysis_time:.2f}s",
                "avg_fill_time": f"{avg_fill_time:.2f}s"
            },
            "detailed_results": self.test_results,
            "special_tests": special_tests
        }

        with open("test_results/wfa_comprehensive_report.json", "w") as f:
            json.dump(report_data, f, indent=2)

        print("\nDetailed report saved to: test_results/wfa_comprehensive_report.json")

    def run_tests(self):
        """Run comprehensive WFA tests"""
        print("Starting WFA Comprehensive Testing")
        print("=" * 60)

        # Create test bid card
        if not self.create_test_bid_card():
            print("Failed to create test bid card")
            return

        try:
            # Test each site
            for site_info in self.test_sites:
                print(f"\n{'='*60}")
                print(f"Testing: {site_info['name']}")
                print(f"URL: {site_info['url']}")
                print(f"Type: {site_info['type']}")
                print(f"Complexity: {site_info['complexity']}")

                # Create test contractor
                contractor = self.create_test_contractor(site_info)
                if not contractor:
                    print(f"Failed to create test contractor for {site_info['name']}")
                    continue

                # Test form analysis
                analysis_result, analysis = self.test_form_analysis(contractor, site_info)

                # Test form filling if form was found
                fill_result = None
                if analysis["has_contact_form"]:
                    fill_result = self.test_form_filling(contractor, site_info, self.test_bid_card)

                # Store results
                self.test_results.append({
                    "site": site_info["name"],
                    "url": site_info["url"],
                    "type": site_info["type"],
                    "complexity": site_info["complexity"],
                    "analysis_result": analysis_result,
                    "fill_result": fill_result
                })

                # Brief pause between tests
                time.sleep(2)

        finally:
            # Always close browser
            self.wfa.stop_browser()

        # Generate report
        self.generate_report()


def main():
    """Run WFA comprehensive tests"""
    # Create test results directory
    os.makedirs("test_results", exist_ok=True)

    # Check if test servers are running
    print("⚠️  IMPORTANT: Make sure test websites are running!")
    print("Run: cd test-sites && start_test_servers.bat")
    print("\nPress Enter to continue...")
    input()

    # Run tests
    tester = WFAComprehensiveTester()
    tester.run_tests()


if __name__ == "__main__":
    main()
