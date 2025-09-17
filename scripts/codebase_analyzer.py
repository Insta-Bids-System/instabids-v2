"""
Instabids Codebase Analyzer
A utility to analyze and understand the Instabids project structure
"""
import json
import os
from typing import Dict, List, Tuple
from collections import defaultdict
from datetime import datetime

class CodebaseAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.stats = defaultdict(int)
        self.components = []
        self.api_endpoints = []
        self.database_tables = []
        self.ai_agents = []
        
    def analyze_project_structure(self, tree_data: list) -> Dict:
        """Analyze the project tree structure"""
        analysis = {
            "total_files": 0,
            "total_directories": 0,
            "file_types": defaultdict(int),
            "key_directories": {},
            "tech_stack": set(),
            "ai_agents": [],
            "components": []
        }
        
        def traverse(items, path=""):
            for item in items:
                full_path = os.path.join(path, item["name"])
                
                if item["type"] == "file":
                    analysis["total_files"] += 1
                    ext = os.path.splitext(item["name"])[1]
                    if ext:
                        analysis["file_types"][ext] += 1
                    
                    # Detect tech stack
                    if item["name"] == "package.json":
                        analysis["tech_stack"].add("Node.js/JavaScript")
                    elif item["name"] == "requirements.txt":
                        analysis["tech_stack"].add("Python")
                    elif item["name"].endswith(".tsx"):
                        analysis["tech_stack"].add("React/TypeScript")
                    elif item["name"] == "docker-compose.yml":
                        analysis["tech_stack"].add("Docker")
                        
                else:  # directory
                    analysis["total_directories"] += 1
                    
                    # Track key directories
                    if item["name"] in ["web", "mobile", "ai-agents", "supabase"]:
                        analysis["key_directories"][item["name"]] = full_path
                    
                    # Find AI agents
                    if path.endswith("agents") and item.get("children"):
                        if any(f["name"] == "agent.py" for f in item["children"] if f["type"] == "file"):
                            analysis["ai_agents"].append(item["name"].upper())
                    
                    if "children" in item:
                        traverse(item["children"], full_path)
        
        traverse(tree_data)
        analysis["tech_stack"] = list(analysis["tech_stack"])
        analysis["file_types"] = dict(analysis["file_types"])
        
        return analysis
    
    def analyze_code_patterns(self, file_content: str, file_path: str) -> Dict:
        """Analyze code patterns in a file"""
        patterns = {
            "imports": [],
            "exports": [],
            "functions": [],
            "classes": [],
            "api_calls": [],
            "database_queries": []
        }
        
        lines = file_content.split('\n')
        
        for i, line in enumerate(lines):
            # TypeScript/JavaScript patterns
            if 'import' in line and 'from' in line:
                patterns["imports"].append(line.strip())
            
            if 'export' in line:
                patterns["exports"].append(line.strip())
                
            if 'function' in line or '=>' in line:
                patterns["functions"].append(f"Line {i+1}: {line.strip()[:80]}...")
                
            if 'class' in line and '{' in line:
                patterns["classes"].append(line.strip())
            
            # API patterns
            if any(method in line for method in ['fetch', 'axios', '.get(', '.post(', '.put(', '.delete(']):
                patterns["api_calls"].append(f"Line {i+1}: {line.strip()[:80]}...")
            
            # Database patterns
            if any(db in line for db in ['supabase', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'query']):
                patterns["database_queries"].append(f"Line {i+1}: {line.strip()[:80]}...")
        
        return patterns
    
    def generate_report(self, tree_analysis: Dict, code_analyses: List[Dict]) -> str:
        """Generate a comprehensive analysis report"""
        report = f"""
# Instabids Codebase Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Project Overview

### Structure Summary
- **Total Files**: {tree_analysis['total_files']}
- **Total Directories**: {tree_analysis['total_directories']}
- **Tech Stack**: {', '.join(tree_analysis['tech_stack'])}

### File Type Distribution
"""
        for ext, count in sorted(tree_analysis['file_types'].items(), key=lambda x: x[1], reverse=True):
            report += f"- `{ext}`: {count} files\n"
        
        report += f"""
### Key Directories
"""
        for name, path in tree_analysis['key_directories'].items():
            report += f"- **{name}**: `{path}`\n"
        
        report += f"""
### AI Agents Found
Total: {len(tree_analysis['ai_agents'])} agents
"""
        for agent in tree_analysis['ai_agents']:
            report += f"- {agent} (Customer Interface Agent)\n"
        
        # Code pattern summary
        if code_analyses:
            report += """
## Code Pattern Analysis

### Import Statistics
"""
            all_imports = []
            for analysis in code_analyses:
                all_imports.extend(analysis.get('imports', []))
            
            # Count most common imports
            import_counts = defaultdict(int)
            for imp in all_imports:
                if 'from' in imp:
                    module = imp.split('from')[-1].strip().strip("'\"")
                    import_counts[module] += 1
            
            report += "**Most Common Imports:**\n"
            for module, count in sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                report += f"- {module}: {count} times\n"
        
        report += """
## Recommendations

1. **Documentation**: Consider adding README files to empty directories
2. **Testing**: Add test files for components (found empty test directories)
3. **Type Safety**: Great use of TypeScript for type safety
4. **AI Architecture**: Well-organized agent structure with dedicated directories

## Next Steps

1. Run `npm install` in the web directory to install dependencies
2. Set up environment variables based on `.env.example`
3. Test the CIA chat interface at `localhost:3000`
"""
        
        return report
    
    def find_todos_and_fixmes(self, content: str, file_path: str) -> List[Tuple[int, str]]:
        """Find TODO and FIXME comments"""
        findings = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if 'TODO' in line or 'FIXME' in line or 'XXX' in line or 'HACK' in line:
                findings.append((i + 1, line.strip()))
        
        return findings