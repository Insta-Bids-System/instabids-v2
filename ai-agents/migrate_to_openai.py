#!/usr/bin/env python3
"""
Migration script to convert Anthropic API usage to OpenAI across the InstaBids codebase
"""

import os
import re

def convert_anthropic_to_openai(file_path):
    """Convert a single file from Anthropic to OpenAI"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Replace imports
        content = re.sub(
            r'from langchain_anthropic import ChatAnthropic',
            'from langchain_openai import ChatOpenAI',
            content
        )
        
        # Replace direct Anthropic imports
        content = re.sub(
            r'from anthropic import Anthropic',
            'from openai import OpenAI',
            content
        )
        
        # Replace model instantiations
        content = re.sub(
            r'ChatAnthropic\(',
            'ChatOpenAI(',
            content
        )
        
        # Replace Anthropic client
        content = re.sub(
            r'Anthropic\(',
            'OpenAI(',
            content
        )
        
        # Replace model names and API keys
        replacements = {
            'claude-opus-4-20250514': 'gpt-4-turbo-preview',
            'claude-3-opus-20240229': 'gpt-4-turbo-preview',
            'claude-3.5-sonnet': 'gpt-4',
            'claude-instant': 'gpt-3.5-turbo',
            'ANTHROPIC_API_KEY': 'OPENAI_API_KEY',
            'anthropic_key': 'openai_key',
            'anthropic_api_key': 'openai_api_key',
        }
        
        for old, new in replacements.items():
            content = re.sub(old, new, content)
        
        # Special handling for vision.py - convert to GPT-4 Vision
        if 'vision.py' in file_path:
            content = re.sub(
                r'client\.messages\.create\(',
                'client.chat.completions.create(',
                content
            )
            # Update model for vision tasks
            content = re.sub(
                r'model="gpt-4-turbo-preview"',
                'model="gpt-4-vision-preview"',
                content
            )
        
        # Update main.py specific checks
        if 'main.py' in file_path:
            # Update the conditional checks
            content = re.sub(
                r'if openai_api_key:',
                'if openai_api_key:',
                content
            )
            # Remove Anthropic-specific fallback
            content = re.sub(
                r'elif openai_api_key:\s*jaa_agent = JobAssessmentAgent\(\)\s*set_jaa_agent\(jaa_agent\)\s*logger\.info\("JAA agent initialized successfully with OpenAI fallback"\)',
                '',
                content
            )
            # Clean up the JAA initialization to use OpenAI only
            content = re.sub(
                r'if openai_api_key:\s*jaa_agent = JobAssessmentAgent\(\)\s*set_jaa_agent\(jaa_agent\)\s*logger\.info\("JAA agent initialized successfully"\)',
                'if openai_api_key:\n        jaa_agent = JobAssessmentAgent()\n        set_jaa_agent(jaa_agent)\n        logger.info("JAA agent initialized successfully with GPT-4")',
                content
            )
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'[CONVERTED] {file_path}')
            return True
        else:
            print(f'[NO CHANGES] {file_path}')
            return False
    except Exception as e:
        print(f'[ERROR] {file_path}: {e}')
        return False

def main():
    """Main migration function"""
    # List of files to convert
    files_to_convert = [
        'agents/jaa/agent.py',
        'agents/cda/agent.py',
        'agents/cda/service_specific_matcher.py',
        'agents/wfa/agent.py',
        'agents/eaa/outreach_channels/mcp_email_channel_claude.py',
        'agents/enrichment/final_real_agent.py',
        'agents/orchestration/claude_check_in_manager.py',
        'agents/automation/followup_automation.py',
        'api/vision.py',
        'main.py'
    ]
    
    print('Starting Anthropic to OpenAI Migration...')
    print('=' * 50)
    
    converted_count = 0
    errors = []
    
    for file_path in files_to_convert:
        if os.path.exists(file_path):
            if convert_anthropic_to_openai(file_path):
                converted_count += 1
        else:
            print(f'[WARNING] File not found: {file_path}')
            errors.append(file_path)
    
    print('=' * 50)
    print(f'Migration Summary:')
    print(f'  - Files converted: {converted_count}')
    print(f'  - Files not found: {len(errors)}')
    
    if errors:
        print('\nFiles that were not found:')
        for error in errors:
            print(f'  - {error}')
    
    print('\n[IMPORTANT] Next Steps:')
    print('1. Update .env file to ensure OPENAI_API_KEY is set')
    print('2. Remove ANTHROPIC_API_KEY from .env (optional)')
    print('3. Test critical agents (JAA, CDA, IRIS)')
    print('4. Monitor API costs for 30-40% expected savings')
    print('5. Update requirements.txt to remove anthropic packages')

if __name__ == "__main__":
    main()