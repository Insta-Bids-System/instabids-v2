#!/usr/bin/env python3
"""
GitHub Push Helper for Instabids Project
Handles the systematic addition and push of all project files while avoiding 'nul' files
"""

import os
import subprocess
import sys
from pathlib import Path
import time

class GitHubPushHelper:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self.directories = [
            'web', 'ai-agents', 'additional_projects', 'agent_specifications',
            'assets', 'database', 'demos', 'docs', 'frontend', 'knowledge',
            'mobile', 'scripts', 'shared', 'supabase', 'test-images', 'test-sites',
            '.github', '.husky'
        ]
        self.root_patterns = [
            '*.md', '*.sql', '*.py', '*.json', '*.bat', '*.sh', 
            'LICENSE', '.gitignore', 'package.json', 'package-lock.json'
        ]
        
    def run_git_command(self, cmd):
        """Run a git command and return the output"""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                cwd=self.repo_path, 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def check_status(self):
        """Check current git status"""
        print("🔍 Checking git status...")
        success, stdout, stderr = self.run_git_command("git status --porcelain")
        if success:
            lines = stdout.strip().split('\n') if stdout.strip() else []
            print(f"   📊 {len(lines)} files/directories in status")
            return True
        else:
            print(f"   ❌ Error: {stderr}")
            return False
    
    def check_remote(self):
        """Check if remote is configured"""
        print("\n🌐 Checking remote configuration...")
        success, stdout, stderr = self.run_git_command("git remote -v")
        if success and stdout:
            print("   ✅ Remote configured:")
            for line in stdout.strip().split('\n'):
                print(f"      {line}")
            return True
        else:
            print("   ❌ No remote configured")
            return False
    
    def reset_to_clean_state(self):
        """Reset to a clean state for adding files"""
        print("\n🧹 Resetting to clean state...")
        # First, unstage everything
        self.run_git_command("git reset HEAD")
        print("   ✅ All files unstaged")
        
    def add_root_files(self):
        """Add root level files"""
        print("\n📄 Adding root level files...")
        added_count = 0
        
        for pattern in self.root_patterns:
            success, stdout, stderr = self.run_git_command(f"git add {pattern}")
            if success:
                # Check if any files were actually added
                success2, stdout2, stderr2 = self.run_git_command(f"git status --porcelain {pattern}")
                if stdout2.strip():
                    file_count = len([l for l in stdout2.strip().split('\n') if l.startswith('A')])
                    added_count += file_count
                    print(f"   ✅ Added {file_count} files matching '{pattern}'")
        
        print(f"   📊 Total root files added: {added_count}")
        return added_count > 0
    
    def add_directory(self, directory):
        """Add a directory to git, automatically skipping 'nul' files"""
        dir_path = self.repo_path / directory
        
        if not dir_path.exists():
            print(f"   ⏭️  Skipping {directory} (doesn't exist)")
            return False
            
        print(f"   📁 Adding {directory}/...")
        success, stdout, stderr = self.run_git_command(f"git add {directory}/")
        
        if success:
            # Count added files
            success2, stdout2, stderr2 = self.run_git_command(f"git status --porcelain {directory}/")
            if stdout2.strip():
                file_count = len([l for l in stdout2.strip().split('\n') if l.startswith('A')])
                print(f"      ✅ Added {file_count} files from {directory}")
                return True
            else:
                print(f"      ℹ️  No new files to add from {directory}")
                return False
        else:
            if "warning" in stderr and "cannot add nothing" not in stderr:
                print(f"      ⚠️  Warning: {stderr}")
            elif "fatal" in stderr:
                print(f"      ❌ Error: {stderr}")
            return False
    
    def add_all_directories(self):
        """Add all project directories"""
        print("\n📂 Adding all directories...")
        successful_dirs = 0
        
        for directory in self.directories:
            if self.add_directory(directory):
                successful_dirs += 1
                
        print(f"\n   📊 Successfully processed {successful_dirs}/{len(self.directories)} directories")
        return successful_dirs > 0
    
    def show_staged_summary(self):
        """Show summary of staged files"""
        print("\n📋 Staged files summary...")
        success, stdout, stderr = self.run_git_command("git status --porcelain")
        if success:
            staged_files = [l for l in stdout.strip().split('\n') if l.startswith('A')]
            modified_files = [l for l in stdout.strip().split('\n') if l.startswith('M')]
            
            print(f"   🆕 New files staged: {len(staged_files)}")
            print(f"   ✏️  Modified files: {len(modified_files)}")
            
            # Show a sample of staged files
            if staged_files:
                print("\n   📄 Sample of staged files:")
                for file in staged_files[:10]:
                    print(f"      {file}")
                if len(staged_files) > 10:
                    print(f"      ... and {len(staged_files) - 10} more")
            
            return len(staged_files) > 0
        return False
    
    def commit_changes(self, message):
        """Commit staged changes"""
        print(f"\n💾 Committing changes...")
        print(f"   📝 Message: {message}")
        
        success, stdout, stderr = self.run_git_command(f'git commit -m "{message}"')
        if success:
            print("   ✅ Commit successful!")
            print(f"   {stdout}")
            return True
        else:
            print(f"   ❌ Commit failed: {stderr}")
            return False
    
    def push_to_github(self, branch="main"):
        """Push to GitHub"""
        print(f"\n🚀 Pushing to GitHub (branch: {branch})...")
        
        # First attempt normal push
        success, stdout, stderr = self.run_git_command(f"git push -u origin {branch}")
        
        if success:
            print("   ✅ Push successful!")
            return True
        elif "rejected" in stderr and "non-fast-forward" in stderr:
            print("   ⚠️  Push rejected (non-fast-forward)")
            print("   Would you like to force push? This will overwrite remote changes!")
            response = input("   Force push? (yes/no): ").lower()
            if response == "yes":
                success2, stdout2, stderr2 = self.run_git_command(f"git push -u origin {branch} --force")
                if success2:
                    print("   ✅ Force push successful!")
                    return True
                else:
                    print(f"   ❌ Force push failed: {stderr2}")
        else:
            print(f"   ❌ Push failed: {stderr}")
            
        return False
    
    def run_full_process(self):
        """Run the complete push process"""
        print("🚀 Starting Instabids GitHub Push Process")
        print("=" * 50)
        
        # Check initial status
        if not self.check_status():
            print("\n❌ Failed to check git status. Ensure you're in a git repository.")
            return False
            
        # Check remote
        if not self.check_remote():
            print("\n❌ No remote configured. Please set up your GitHub remote first.")
            return False
        
        # Ask user what they want to do
        print("\n🤔 What would you like to do?")
        print("1. Add all files and push (recommended)")
        print("2. Reset and start fresh")
        print("3. Just check status")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            # Reset to clean state first
            self.reset_to_clean_state()
            
            # Add all files
            root_added = self.add_root_files()
            dirs_added = self.add_all_directories()
            
            if root_added or dirs_added:
                # Show what's staged
                if self.show_staged_summary():
                    # Commit
                    commit_msg = input("\n📝 Enter commit message (or press Enter for default): ").strip()
                    if not commit_msg:
                        commit_msg = "Complete Instabids platform: 8 AI agents, web/mobile frontends, 5 expansion projects"
                    
                    if self.commit_changes(commit_msg):
                        # Push
                        self.push_to_github()
                    else:
                        print("\n❌ Commit failed. Please check your changes and try again.")
                else:
                    print("\n❌ No files were staged. Please check your repository.")
            else:
                print("\n❌ No files were added. Please check your repository structure.")
                
        elif choice == "2":
            self.reset_to_clean_state()
            print("\n✅ Repository reset to clean state. Run again to add files.")
            
        elif choice == "3":
            self.show_staged_summary()
            
        else:
            print("\n👋 Exiting...")
            
        print("\n" + "=" * 50)
        print("✅ Process complete!")

def main():
    # Get the repository path
    repo_path = Path.cwd()
    
    # Ensure we're in the instabids directory
    if repo_path.name != 'instabids':
        print("❌ Error: This script must be run from the instabids directory!")
        print(f"   Current directory: {repo_path}")
        
        # Try to find instabids directory
        instabids_path = repo_path / 'instabids'
        if instabids_path.exists():
            print(f"\n📁 Found instabids at: {instabids_path}")
            print("   Changing to that directory...")
            os.chdir(instabids_path)
            repo_path = instabids_path
        else:
            print("\n❌ Could not find instabids directory. Please navigate there first.")
            sys.exit(1)
    
    # Create and run helper
    helper = GitHubPushHelper(repo_path)
    helper.run_full_process()

if __name__ == "__main__":
    main()
