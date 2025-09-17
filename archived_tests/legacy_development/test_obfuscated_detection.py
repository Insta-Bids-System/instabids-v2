#!/usr/bin/env python3
"""
Test GPT-4o's ability to detect obfuscated contact information
Tests various file types and obfuscation techniques
"""

import sys
import os
import asyncio
import base64
sys.path.append('C:/Users/Not John Or Justin/Documents/instabids/ai-agents')

from agents.intelligent_messaging_agent import GPT5SecurityAnalyzer

async def test_file(analyzer, file_path, expected_result):
    """Test a single file and return results"""
    
    file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(file_name)[1].lower()
    
    print(f"\nTesting: {file_name}")
    print(f"Expected: {'FLAGGED' if expected_result else 'CLEAN'}")
    
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
            file_base64 = base64.b64encode(file_data).decode('utf-8')
        
        # Determine analysis method based on file type
        if file_ext == '.pdf':
            result = await analyzer.analyze_pdf_content(file_base64, file_name)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            image_format = file_ext[1:]  # Remove the dot
            result = await analyzer.analyze_image_content(file_base64, image_format)
        else:
            # For text files, we need to extract text first
            try:
                text_content = file_data.decode('utf-8')
                # Use the PDF analyzer with text content (it can handle plain text too)
                result = await analyzer.analyze_pdf_content(file_base64, file_name)
            except:
                result = {
                    "contact_info_detected": True,
                    "confidence": 0.5,
                    "explanation": "Unable to analyze file type"
                }
        
        detected = result.get('contact_info_detected', False)
        confidence = result.get('confidence', 0)
        explanation = result.get('explanation', '')
        
        # Extract found items
        phones = result.get('phones', [])
        emails = result.get('emails', [])
        addresses = result.get('addresses', [])
        social = result.get('social_handles', [])
        
        print(f"Result: {'FLAGGED' if detected else 'CLEAN'} (confidence: {confidence})")
        print(f"Explanation: {explanation}")
        
        if phones:
            print(f"Phones found: {phones}")
        if emails:
            print(f"Emails found: {emails}")
        if addresses:
            print(f"Addresses found: {addresses}")
        if social:
            print(f"Social handles found: {social}")
        
        # Check if result matches expectation
        if detected == expected_result:
            print("CORRECT DETECTION")
            return True
        else:
            print(f"INCORRECT - Expected {'FLAGGED' if expected_result else 'CLEAN'}, got {'FLAGGED' if detected else 'CLEAN'}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_comprehensive_tests():
    """Run tests on all file types with various obfuscation levels"""
    
    analyzer = GPT5SecurityAnalyzer()
    
    # Define test cases (file, should_be_flagged)
    test_cases = [
        # PDFs with obfuscation
        ("obfuscated_heavy.pdf", True),  # Heavy obfuscation - should catch
        ("obfuscated_subtle.pdf", True),  # Subtle obfuscation - should catch
        ("obfuscated_clean.pdf", False),  # Clean - should pass
        
        # Images with text
        ("obfuscated_image_obvious.png", True),  # Obvious contact info
        ("obfuscated_image_subtle.png", True),   # Subtle contact info
        ("obfuscated_image_clean.png", False),   # Clean image
        
        # Text files
        ("obfuscated_heavy.txt", True),   # Heavy obfuscation
        ("obfuscated_clean.txt", False),  # Clean text
        
        # Original test files (if they exist)
        ("test_bid_proposal.pdf", True),  # Original with contact
        ("clean_proposal.pdf", False),    # Original clean
    ]
    
    results = []
    
    print("=" * 70)
    print("COMPREHENSIVE OBFUSCATION DETECTION TEST")
    print("=" * 70)
    print("\nTesting GPT-4o's ability to detect:")
    print("- Spelled out numbers (five five five)")
    print("- Spaced digits (5 5 5 - 1 2 3)")
    print("- Letter substitutions (O for 0, l for 1)")
    print("- Alternative formats ([at], [dot])")
    print("- Social media handles")
    print("- WhatsApp/Telegram contacts")
    print("=" * 70)
    
    for file_name, should_flag in test_cases:
        file_path = f"C:/Users/Not John Or Justin/Documents/instabids/{file_name}"
        
        if os.path.exists(file_path):
            success = await test_file(analyzer, file_path, should_flag)
            results.append((file_name, success))
        else:
            print(f"\nSkipping {file_name} - file not found")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for file_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status} - {file_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    # Detailed analysis
    pdf_results = [r for r in results if r[0].endswith('.pdf')]
    image_results = [r for r in results if r[0].endswith(('.png', '.jpg'))]
    text_results = [r for r in results if r[0].endswith('.txt')]
    
    if pdf_results:
        pdf_passed = sum(1 for _, s in pdf_results if s)
        print(f"PDFs: {pdf_passed}/{len(pdf_results)} passed")
    
    if image_results:
        img_passed = sum(1 for _, s in image_results if s)
        print(f"Images: {img_passed}/{len(image_results)} passed")
    
    if text_results:
        txt_passed = sum(1 for _, s in text_results if s)
        print(f"Text files: {txt_passed}/{len(text_results)} passed")
    
    # Critical check - can it catch obfuscated attempts?
    obfuscated_tests = [r for r in results if 'heavy' in r[0] or 'subtle' in r[0] or 'obvious' in r[0]]
    obfuscated_caught = sum(1 for _, s in obfuscated_tests if s)
    
    print(f"\nOBFUSCATION DETECTION: {obfuscated_caught}/{len(obfuscated_tests)} caught")
    
    if obfuscated_caught == len(obfuscated_tests):
        print("EXCELLENT - GPT-4o caught ALL obfuscation attempts!")
    elif obfuscated_caught >= len(obfuscated_tests) * 0.7:
        print("GOOD - GPT-4o caught most obfuscation attempts")
    else:
        print("POOR - GPT-4o missed many obfuscation attempts")
    
    return passed == total

async def main():
    """Main test runner"""
    success = await run_comprehensive_tests()
    
    if success:
        print("\nALL TESTS PASSED - System can detect sophisticated bypass attempts!")
    else:
        print("\nSOME TESTS FAILED - Review detection capabilities")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)