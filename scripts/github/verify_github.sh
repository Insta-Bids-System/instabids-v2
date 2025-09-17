#!/bin/bash
# Instabids GitHub Verification Script

echo "🔍 Verifying Instabids GitHub Repository..."
echo "==========================================="

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed!"
    exit 1
fi

cd "C:\Users\Not John Or Justin\Documents\instabids"

# Check current branch
echo "📌 Current Branch:"
git branch --show-current

# Check remote
echo -e "\n📡 Remote Repository:"
git remote -v

# Count files
echo -e "\n📊 Repository Statistics:"
echo "Total files: $(git ls-files | wc -l)"
echo "AI Agent files: $(git ls-files ai-agents/agents | wc -l)"
echo "Frontend files: $(git ls-files web/src | wc -l)"
echo "Database migrations: $(git ls-files supabase/migrations | wc -l)"

# Check for secrets in committed files
echo -e "\n🔒 Security Check:"
if git grep -i "sk-ant-api03" > /dev/null 2>&1; then
    echo "⚠️ WARNING: Found API keys in committed files!"
else
    echo "✅ No API keys found in committed files"
fi

# List key directories
echo -e "\n📁 Key Directories:"
for dir in "ai-agents/agents" "web/src" "supabase/migrations" "agent_specifications"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir exists"
    else
        echo "❌ $dir missing!"
    fi
done

echo -e "\n✅ Verification Complete!"
echo "🔗 Repository URL: https://github.com/Insta-Bids-System/instabids"
