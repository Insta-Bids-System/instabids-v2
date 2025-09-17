#!/usr/bin/env python3
"""
Generate current project context for AI agents
Run this before every session to understand system state
"""
import os
import subprocess
import json
from pathlib import Path

def get_active_processes():
    """Find active Python processes and ports"""
    try:
        # Get Python processes
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        python_procs = len([line for line in result.stdout.split('\n') if 'python.exe' in line])
        
        # Get port usage
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        ports_8000 = len([line for line in result.stdout.split('\n') if ':8000' in line and 'LISTENING' in line])
        ports_8007 = len([line for line in result.stdout.split('\n') if ':8007' in line and 'LISTENING' in line])
        
        return {
            'python_processes': python_procs,
            'port_8000_active': ports_8000 > 0,
            'port_8007_active': ports_8007 > 0
        }
    except:
        return {'error': 'Could not check processes'}

def scan_project_structure():
    """Scan project structure and identify systems"""
    root = Path('.')
    
    systems = {}
    
    # Check ai-agents system
    ai_agents_main = root / 'ai-agents' / 'main.py'
    ai_agents_cia = root / 'ai-agents' / 'agents' / 'cia' / 'agent.py'
    ai_agents_db = root / 'ai-agents' / 'database_simple.py'
    
    systems['ai_agents'] = {
        'exists': ai_agents_main.exists(),
        'main_server': ai_agents_main.exists(),
        'cia_agent': ai_agents_cia.exists(),
        'database': ai_agents_db.exists(),
        'complete': all([ai_agents_main.exists(), ai_agents_cia.exists(), ai_agents_db.exists()])
    }
    
    # Check backend system
    backend_main = root / 'backend' / 'main.py'
    backend_cia = root / 'backend' / 'agents' / 'cia.py'
    
    systems['backend'] = {
        'exists': backend_main.exists(),
        'main_server': backend_main.exists(),
        'cia_agent': backend_cia.exists(),
        'complete': all([backend_main.exists(), backend_cia.exists()])
    }
    
    # Check web system
    web_package = root / 'web' / 'package.json'
    web_src = root / 'web' / 'src'
    
    systems['web'] = {
        'exists': web_package.exists(),
        'package_json': web_package.exists(),
        'src_dir': web_src.exists(),
        'complete': all([web_package.exists(), web_src.exists()])
    }
    
    return systems

def check_api_keys():
    """Check if required API keys are present"""
    keys = {}
    
    # Check ai-agents .env
    ai_env = Path('ai-agents') / '.env'
    backend_env = Path('backend') / '.env'
    root_env = Path('.env')
    
    keys['locations'] = {
        'ai_agents_env': ai_env.exists(),
        'backend_env': backend_env.exists(),
        'root_env': root_env.exists()
    }
    
    # Check actual environment
    keys['loaded'] = {
        'anthropic_key': bool(os.getenv('ANTHROPIC_API_KEY')),
        'supabase_url': bool(os.getenv('SUPABASE_URL')),
        'supabase_key': bool(os.getenv('SUPABASE_ANON_KEY'))
    }
    
    return keys

def generate_context():
    """Generate complete project context"""
    context = {
        'timestamp': str(Path.cwd()),
        'processes': get_active_processes(),
        'systems': scan_project_structure(),
        'api_keys': check_api_keys(),
        'recommendations': []
    }
    
    # Generate recommendations
    if context['systems']['ai_agents']['complete'] and not context['processes']['port_8000_active']:
        context['recommendations'].append("✅ Original ai-agents system is complete but not running. Start with: cd ai-agents && python main.py")
    
    if context['systems']['backend']['exists'] and context['processes']['port_8007_active']:
        context['recommendations'].append("⚠️ backend system is running on port 8007 - this is likely a test/broken system")
    
    if not context['systems']['ai_agents']['complete']:
        context['recommendations'].append("🚨 Original ai-agents system is incomplete or missing")
    
    if context['processes']['python_processes'] > 3:
        context['recommendations'].append(f"⚠️ {context['processes']['python_processes']} Python processes running - may need cleanup")
    
    return context

def main():
    """Main function"""
    print("🔍 Scanning Instabids project structure...")
    
    context = generate_context()
    
    # Write to file
    with open('CURRENT_PROJECT_CONTEXT.json', 'w') as f:
        json.dump(context, f, indent=2)
    
    # Print summary
    print("\n📊 PROJECT CONTEXT SUMMARY")
    print("=" * 50)
    
    print(f"📁 Systems Found:")
    for name, system in context['systems'].items():
        status = "✅ COMPLETE" if system['complete'] else "❌ INCOMPLETE"
        print(f"   {name}: {status}")
    
    print(f"\n🔌 Active Processes:")
    print(f"   Python processes: {context['processes']['python_processes']}")
    print(f"   Port 8000 (expected): {'✅' if context['processes']['port_8000_active'] else '❌'}")
    print(f"   Port 8007 (test): {'⚠️ ACTIVE' if context['processes']['port_8007_active'] else '✅ INACTIVE'}")
    
    print(f"\n🔑 API Keys:")
    for location, exists in context['api_keys']['locations'].items():
        print(f"   {location}: {'✅' if exists else '❌'}")
    
    print(f"\n💡 Recommendations:")
    for rec in context['recommendations']:
        print(f"   {rec}")
    
    print(f"\n📄 Full context saved to: CURRENT_PROJECT_CONTEXT.json")

if __name__ == "__main__":
    main()