#!/usr/bin/env python3
"""
Docker Helper for InstaBids - Uses Desktop Commander MCP
Provides easy Docker management functions for debugging and testing
"""

import subprocess
import json
import sys
from pathlib import Path

class DockerHelper:
    def __init__(self, project_dir="C:\\Users\\Not John Or Justin\\Documents\\instabids"):
        self.project_dir = Path(project_dir)
    
    def run_command(self, cmd, cwd=None):
        """Run a command and return output"""
        try:
            if cwd is None:
                cwd = self.project_dir
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                cwd=cwd,
                timeout=30
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            return "", str(e), 1
    
    def ps(self, all_containers=False):
        """List running containers"""
        cmd = "docker-compose ps" if not all_containers else "docker-compose ps -a"
        stdout, stderr, code = self.run_command(cmd)
        print("=== CONTAINER STATUS ===")
        print(stdout if stdout else stderr)
        return stdout, stderr, code
    
    def logs(self, service=None, tail=50):
        """Get container logs"""
        if service:
            cmd = f"docker-compose logs --tail={tail} {service}"
        else:
            cmd = f"docker-compose logs --tail={tail}"
        
        stdout, stderr, code = self.run_command(cmd)
        print(f"=== LOGS {'FOR ' + service.upper() if service else 'ALL SERVICES'} ===")
        print(stdout if stdout else stderr)
        return stdout, stderr, code
    
    def restart(self, service=None):
        """Restart services"""
        if service:
            cmd = f"docker-compose restart {service}"
        else:
            cmd = "docker-compose restart"
        
        stdout, stderr, code = self.run_command(cmd)
        print(f"=== RESTART {'SERVICE: ' + service.upper() if service else 'ALL SERVICES'} ===")
        print(stdout if stdout else stderr)
        return stdout, stderr, code
    
    def exec_command(self, service, command):
        """Execute command in container"""
        cmd = f"docker-compose exec {service} {command}"
        stdout, stderr, code = self.run_command(cmd)
        print(f"=== EXEC IN {service.upper()}: {command} ===")
        print(stdout if stdout else stderr)
        return stdout, stderr, code
    
    def health_check(self):
        """Complete health check of all services"""
        print("🐳 InstaBids Docker Health Check")
        print("=" * 50)
        
        # Check container status
        print("\n1. Container Status:")
        self.ps()
        
        # Check each service
        services = ["instabids-backend", "instabids-frontend", "supabase", "mailhog"]
        
        for service in services:
            print(f"\n2. {service.upper()} Health:")
            # Try to get recent logs to see if service is healthy
            stdout, stderr, code = self.logs(service, tail=10)
            
            if "error" in stdout.lower() or "failed" in stdout.lower():
                print(f"⚠️  {service} may have issues - check logs above")
            else:
                print(f"✅ {service} appears healthy")
        
        # Test API endpoints
        print("\n3. API Connectivity Tests:")
        self.test_endpoints()
    
    def test_endpoints(self):
        """Test key endpoints"""
        endpoints = [
            ("Backend API", "curl -s http://localhost:8008/ || echo 'FAILED'"),
            ("Frontend", "curl -s -I http://localhost:5173 | head -1 || echo 'FAILED'"),
            ("MailHog", "curl -s -I http://localhost:8080 | head -1 || echo 'FAILED'")
        ]
        
        for name, cmd in endpoints:
            stdout, stderr, code = self.run_command(cmd)
            status = "✅ HEALTHY" if "200 OK" in stdout or "Instabids API" in stdout else "❌ FAILED"
            print(f"   {name}: {status}")
            if stderr or "FAILED" in stdout:
                print(f"      Error: {stderr or stdout}")

def main():
    docker = DockerHelper()
    
    if len(sys.argv) < 2:
        print("Usage: python docker-helper.py <command>")
        print("Commands:")
        print("  health    - Complete health check")
        print("  ps        - List containers")
        print("  logs [service] - Show logs")
        print("  restart [service] - Restart service")
        print("  exec <service> <command> - Execute command in container")
        return
    
    command = sys.argv[1]
    
    if command == "health":
        docker.health_check()
    elif command == "ps":
        docker.ps()
    elif command == "logs":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        docker.logs(service)
    elif command == "restart":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        docker.restart(service)
    elif command == "exec" and len(sys.argv) >= 4:
        service = sys.argv[2]
        cmd = " ".join(sys.argv[3:])
        docker.exec_command(service, cmd)
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()