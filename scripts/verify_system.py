#!/usr/bin/env python3
"""
System Verification Script

This script performs comprehensive verification of all Game Telegram system components:
- Service health checks
- Database connectivity
- API endpoint validation
- Configuration verification
- Integration testing
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
import psycopg2
import redis
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

class SystemVerifier:
    """Comprehensive system verification."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "unknown",
            "checks": {},
            "errors": [],
            "warnings": []
        }
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_result(self, check_name: str, status: str, details: str = "", error: str = ""):
        """Log verification result."""
        self.results["checks"][check_name] = {
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        status_emoji = {
            "pass": "✅",
            "fail": "❌", 
            "warning": "⚠️",
            "skip": "⏭️"
        }
        
        print(f"{status_emoji.get(status, '❓')} {check_name}: {details}")
        if error:
            print(f"   Error: {error}")
            self.results["errors"].append(f"{check_name}: {error}")
    
    def get_env_var(self, var_name: str, default: str = None) -> Optional[str]:
        """Get environment variable with fallback."""
        value = os.getenv(var_name, default)
        if not value and not default:
            self.log_result(
                f"env_var_{var_name.lower()}", 
                "fail", 
                f"Missing required environment variable: {var_name}"
            )
        return value
    
    async def verify_environment_config(self) -> bool:
        """Verify environment configuration."""
        print("\n🔧 Verifying Environment Configuration...")
        
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL", 
            "SECRET_KEY",
            "JWT_SECRET",
            "ADMIN_BOT_TOKEN",
            "PLAYER_BOT_TOKEN"
        ]
        
        optional_vars = [
            "DEBUG",
            "LOG_LEVEL",
            "ALLOWED_HOSTS",
            "CORS_ORIGINS"
        ]
        
        all_good = True
        
        # Check required variables
        for var in required_vars:
            value = self.get_env_var(var)
            if value:
                # Mask sensitive values
                display_value = value[:10] + "..." if len(value) > 10 else value
                if "token" in var.lower() or "secret" in var.lower() or "password" in var.lower():
                    display_value = "*" * 8
                self.log_result(f"env_{var.lower()}", "pass", f"Set: {display_value}")
            else:
                self.log_result(f"env_{var.lower()}", "fail", f"Missing required variable")
                all_good = False
        
        # Check optional variables
        for var in optional_vars:
            value = self.get_env_var(var, "not_set")
            if value != "not_set":
                self.log_result(f"env_{var.lower()}", "pass", f"Set: {value}")
            else:
                self.log_result(f"env_{var.lower()}", "warning", "Not set (using defaults)")
        
        return all_good
    
    async def verify_database_connectivity(self) -> bool:
        """Verify database connectivity and basic operations."""
        print("\n🗄️ Verifying Database Connectivity...")
        
        database_url = self.get_env_var("DATABASE_URL")
        if not database_url:
            self.log_result("database_connection", "fail", "No DATABASE_URL configured")
            return False
        
        try:
            # Test connection
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            self.log_result("database_connection", "pass", f"Connected: {version[:50]}...")
            
            # Test table existence (basic structure check)
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name IN ('games', 'users', 'game_results')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['games', 'users', 'game_results']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                self.log_result("database_schema", "warning", f"Missing tables: {missing_tables}")
            else:
                self.log_result("database_schema", "pass", "Core tables exist")
            
            # Test write operation
            cursor.execute("CREATE TEMP TABLE test_table (id SERIAL PRIMARY KEY, test_data TEXT);")
            cursor.execute("INSERT INTO test_table (test_data) VALUES ('verification_test');")
            cursor.execute("SELECT test_data FROM test_table WHERE test_data = 'verification_test';")
            result = cursor.fetchone()
            
            if result and result[0] == 'verification_test':
                self.log_result("database_write", "pass", "Write operations working")
            else:
                self.log_result("database_write", "fail", "Write operations failed")
                return False
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.log_result("database_connection", "fail", "Connection failed", str(e))
            return False
    
    async def verify_redis_connectivity(self) -> bool:
        """Verify Redis connectivity and operations."""
        print("\n🔴 Verifying Redis Connectivity...")
        
        redis_url = self.get_env_var("REDIS_URL")
        if not redis_url:
            self.log_result("redis_connection", "fail", "No REDIS_URL configured")
            return False
        
        try:
            # Test connection
            r = redis.from_url(redis_url)
            
            # Test ping
            if r.ping():
                self.log_result("redis_connection", "pass", "Connected and responding")
            else:
                self.log_result("redis_connection", "fail", "Connection failed")
                return False
            
            # Test basic operations
            test_key = "verification_test"
            test_value = "system_check"
            
            # Set and get
            r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            retrieved_value = r.get(test_key)
            
            if retrieved_value and retrieved_value.decode() == test_value:
                self.log_result("redis_operations", "pass", "Read/write operations working")
            else:
                self.log_result("redis_operations", "fail", "Read/write operations failed")
                return False
            
            # Clean up
            r.delete(test_key)
            
            # Test memory info
            info = r.info('memory')
            used_memory = info.get('used_memory_human', 'unknown')
            self.log_result("redis_memory", "pass", f"Memory usage: {used_memory}")
            
            return True
            
        except Exception as e:
            self.log_result("redis_connection", "fail", "Connection failed", str(e))
            return False
    
    async def verify_service_health(self, service_name: str, port: int) -> bool:
        """Verify individual service health."""
        try:
            response = await self.client.get(f"http://localhost:{port}/health")
            
            if response.status_code == 200:
                try:
                    health_data = response.json()
                    status = health_data.get("status", "unknown")
                    self.log_result(f"{service_name}_health", "pass", f"Status: {status}")
                    return True
                except:
                    self.log_result(f"{service_name}_health", "pass", "Responding (non-JSON)")
                    return True
            else:
                self.log_result(f"{service_name}_health", "fail", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result(f"{service_name}_health", "fail", "Service unreachable", str(e))
            return False
    
    async def verify_all_services(self) -> bool:
        """Verify all microservices are healthy."""
        print("\n🚀 Verifying Service Health...")
        
        services = [
            ("game-engine", 8002),
            ("session-manager", 8003), 
            ("user-manager", 8004),
            ("analytics-service", 8005),
            ("notification-service", 8006)
        ]
        
        all_healthy = True
        
        for service_name, port in services:
            healthy = await self.verify_service_health(service_name, port)
            if not healthy:
                all_healthy = False
        
        return all_healthy
    
    async def verify_api_endpoints(self) -> bool:
        """Verify critical API endpoints."""
        print("\n🌐 Verifying API Endpoints...")
        
        endpoints = [
            ("GET", "http://localhost:8002/api/v1/games", "List games"),
            ("GET", "http://localhost:8003/api/v1/sessions", "List sessions"),
            ("GET", "http://localhost:8004/api/v1/users", "List users"),
            ("GET", "http://localhost:8005/api/v1/analytics/summary", "Analytics summary"),
        ]
        
        all_working = True
        
        for method, url, description in endpoints:
            try:
                if method == "GET":
                    response = await self.client.get(url)
                else:
                    response = await self.client.request(method, url)
                
                if response.status_code in [200, 401, 403]:  # 401/403 are OK (auth required)
                    self.log_result(f"api_{description.lower().replace(' ', '_')}", "pass", f"HTTP {response.status_code}")
                else:
                    self.log_result(f"api_{description.lower().replace(' ', '_')}", "fail", f"HTTP {response.status_code}")
                    all_working = False
                    
            except Exception as e:
                self.log_result(f"api_{description.lower().replace(' ', '_')}", "fail", "Request failed", str(e))
                all_working = False
        
        return all_working
    
    async def verify_bot_tokens(self) -> bool:
        """Verify Telegram bot tokens."""
        print("\n🤖 Verifying Bot Tokens...")
        
        admin_token = self.get_env_var("ADMIN_BOT_TOKEN")
        player_token = self.get_env_var("PLAYER_BOT_TOKEN")
        
        all_valid = True
        
        for bot_name, token in [("admin", admin_token), ("player", player_token)]:
            if not token:
                self.log_result(f"bot_token_{bot_name}", "fail", "Token not configured")
                all_valid = False
                continue
            
            try:
                response = await self.client.get(f"https://api.telegram.org/bot{token}/getMe")
                
                if response.status_code == 200:
                    bot_info = response.json()
                    if bot_info.get("ok"):
                        bot_username = bot_info["result"]["username"]
                        self.log_result(f"bot_token_{bot_name}", "pass", f"Valid: @{bot_username}")
                    else:
                        self.log_result(f"bot_token_{bot_name}", "fail", "Invalid token")
                        all_valid = False
                else:
                    self.log_result(f"bot_token_{bot_name}", "fail", f"HTTP {response.status_code}")
                    all_valid = False
                    
            except Exception as e:
                self.log_result(f"bot_token_{bot_name}", "fail", "Verification failed", str(e))
                all_valid = False
        
        return all_valid
    
    async def verify_file_structure(self) -> bool:
        """Verify critical file structure."""
        print("\n📁 Verifying File Structure...")
        
        critical_files = [
            "docker-compose.yml",
            ".env.example",
            "requirements.txt",
            "services/game-engine/app/main.py",
            "services/player-bot/app/main.py",
            "services/admin-bot/app/main.py",
            "shared/models/base.py",
            "tests/conftest.py"
        ]
        
        critical_dirs = [
            "services",
            "shared",
            "tests",
            "docs",
            "demo"
        ]
        
        all_present = True
        
        # Check files
        for file_path in critical_files:
            if Path(file_path).exists():
                self.log_result(f"file_{file_path.replace('/', '_').replace('.', '_')}", "pass", "Exists")
            else:
                self.log_result(f"file_{file_path.replace('/', '_').replace('.', '_')}", "fail", "Missing")
                all_present = False
        
        # Check directories
        for dir_path in critical_dirs:
            if Path(dir_path).is_dir():
                file_count = len(list(Path(dir_path).rglob("*")))
                self.log_result(f"dir_{dir_path}", "pass", f"Exists ({file_count} files)")
            else:
                self.log_result(f"dir_{dir_path}", "fail", "Missing")
                all_present = False
        
        return all_present
    
    async def verify_documentation(self) -> bool:
        """Verify documentation completeness."""
        print("\n📚 Verifying Documentation...")
        
        doc_files = [
            "README.md",
            "docs/user-guide/admin-guide.md",
            "docs/user-guide/player-guide.md", 
            "docs/developer-guide/api-reference.md",
            "docs/developer-guide/developer-guide.md",
            "docs/deployment/deployment-guide.md"
        ]
        
        all_present = True
        
        for doc_file in doc_files:
            if Path(doc_file).exists():
                size = Path(doc_file).stat().st_size
                self.log_result(f"doc_{doc_file.replace('/', '_').replace('.', '_')}", "pass", f"Exists ({size} bytes)")
            else:
                self.log_result(f"doc_{doc_file.replace('/', '_').replace('.', '_')}", "fail", "Missing")
                all_present = False
        
        return all_present
    
    async def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run all verification checks."""
        print("🔍 Starting Comprehensive System Verification")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all verification checks
        checks = [
            ("Environment Configuration", self.verify_environment_config()),
            ("Database Connectivity", self.verify_database_connectivity()),
            ("Redis Connectivity", self.verify_redis_connectivity()),
            ("Service Health", self.verify_all_services()),
            ("API Endpoints", self.verify_api_endpoints()),
            ("Bot Tokens", self.verify_bot_tokens()),
            ("File Structure", self.verify_file_structure()),
            ("Documentation", self.verify_documentation())
        ]
        
        results = []
        for check_name, check_coro in checks:
            try:
                result = await check_coro
                results.append(result)
            except Exception as e:
                self.log_result(f"check_{check_name.lower().replace(' ', '_')}", "fail", "Check failed", str(e))
                results.append(False)
        
        # Calculate overall status
        total_checks = len([check for check in self.results["checks"].values()])
        passed_checks = len([check for check in self.results["checks"].values() if check["status"] == "pass"])
        failed_checks = len([check for check in self.results["checks"].values() if check["status"] == "fail"])
        warning_checks = len([check for check in self.results["checks"].values() if check["status"] == "warning"])
        
        if failed_checks == 0:
            if warning_checks == 0:
                overall_status = "excellent"
            else:
                overall_status = "good"
        elif failed_checks <= total_checks * 0.2:  # Less than 20% failed
            overall_status = "acceptable"
        else:
            overall_status = "poor"
        
        self.results["overall_status"] = overall_status
        self.results["summary"] = {
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": failed_checks,
            "warnings": warning_checks,
            "duration_seconds": round(time.time() - start_time, 2)
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 60)
        
        status_colors = {
            "excellent": "🟢",
            "good": "🟡", 
            "acceptable": "🟠",
            "poor": "🔴"
        }
        
        print(f"{status_colors.get(overall_status, '❓')} Overall Status: {overall_status.upper()}")
        print(f"✅ Passed: {passed_checks}/{total_checks}")
        print(f"❌ Failed: {failed_checks}/{total_checks}")
        print(f"⚠️ Warnings: {warning_checks}/{total_checks}")
        print(f"⏱️ Duration: {self.results['summary']['duration_seconds']}s")
        
        if self.results["errors"]:
            print(f"\n🚨 Critical Issues:")
            for error in self.results["errors"][:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(self.results["errors"]) > 5:
                print(f"   ... and {len(self.results['errors']) - 5} more")
        
        return self.results

async def main():
    """Main verification function."""
    try:
        async with SystemVerifier() as verifier:
            results = await verifier.run_comprehensive_verification()
            
            # Save results to file
            results_file = Path("verification_results.json")
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n💾 Detailed results saved to: {results_file}")
            
            # Exit with appropriate code
            if results["overall_status"] in ["excellent", "good"]:
                print("\n🎉 System verification completed successfully!")
                return 0
            elif results["overall_status"] == "acceptable":
                print("\n⚠️ System verification completed with warnings.")
                return 1
            else:
                print("\n❌ System verification failed. Please address the issues above.")
                return 2
                
    except KeyboardInterrupt:
        print("\n❌ Verification cancelled by user")
        return 130
    except Exception as e:
        print(f"\n💥 Verification failed with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)