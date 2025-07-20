#!/usr/bin/env python3
"""
Release packaging script for Game Telegram project.
Creates versioned releases with all necessary components.
"""

import os
import sys
import json
import shutil
import tarfile
import zipfile
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
RELEASE_DIR = PROJECT_ROOT / "releases"
VERSION_FILE = PROJECT_ROOT / "VERSION"

class ReleaseManager:
    """Manages the release packaging process."""
    
    def __init__(self, version: str, release_type: str = "stable"):
        self.version = version
        self.release_type = release_type
        self.release_name = f"game-telegram-{version}"
        self.release_path = RELEASE_DIR / self.release_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def create_release(self) -> bool:
        """Create a complete release package."""
        try:
            print(f"Creating release {self.release_name}...")
            
            # Create release directory
            self.release_path.mkdir(parents=True, exist_ok=True)
            
            # Copy core files
            self._copy_core_files()
            
            # Copy services
            self._copy_services()
            
            # Copy shared components
            self._copy_shared_components()
            
            # Copy documentation
            self._copy_documentation()
            
            # Copy tests
            self._copy_tests()
            
            # Copy demo data
            self._copy_demo_data()
            
            # Copy scripts
            self._copy_scripts()
            
            # Copy configuration files
            self._copy_configuration()
            
            # Create release metadata
            self._create_release_metadata()
            
            # Create installation script
            self._create_installation_script()
            
            # Create archives
            self._create_archives()
            
            # Create checksums
            self._create_checksums()
            
            print(f"✅ Release {self.release_name} created successfully!")
            print(f"📁 Location: {self.release_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating release: {e}")
            return False
    
    def _copy_core_files(self):
        """Copy core project files."""
        print("📋 Copying core files...")
        
        core_files = [
            "README.md",
            "LICENSE",
            "docker-compose.yml",
            "docker-compose.test.yml",
            "docker-compose.prod.yml",
            ".env.example",
            "requirements.txt",
            "Makefile",
            "pytest.ini",
            ".gitignore",
            ".pre-commit-config.yaml"
        ]
        
        for file in core_files:
            src = PROJECT_ROOT / file
            if src.exists():
                shutil.copy2(src, self.release_path / file)
    
    def _copy_services(self):
        """Copy all microservices."""
        print("🔧 Copying services...")
        
        services_dir = PROJECT_ROOT / "services"
        if services_dir.exists():
            shutil.copytree(
                services_dir,
                self.release_path / "services",
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.pyo", ".pytest_cache",
                    "node_modules", ".coverage", "htmlcov"
                )
            )
    
    def _copy_shared_components(self):
        """Copy shared components."""
        print("📦 Copying shared components...")
        
        shared_dir = PROJECT_ROOT / "shared"
        if shared_dir.exists():
            shutil.copytree(
                shared_dir,
                self.release_path / "shared",
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.pyo", ".pytest_cache"
                )
            )
    
    def _copy_documentation(self):
        """Copy documentation."""
        print("📚 Copying documentation...")
        
        docs_dir = PROJECT_ROOT / "docs"
        if docs_dir.exists():
            shutil.copytree(docs_dir, self.release_path / "docs")
    
    def _copy_tests(self):
        """Copy test suite."""
        print("🧪 Copying tests...")
        
        tests_dir = PROJECT_ROOT / "tests"
        if tests_dir.exists():
            shutil.copytree(
                tests_dir,
                self.release_path / "tests",
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.pyo", ".pytest_cache",
                    ".coverage", "htmlcov"
                )
            )
    
    def _copy_demo_data(self):
        """Copy demo data and examples."""
        print("🎮 Copying demo data...")
        
        demo_dir = PROJECT_ROOT / "demo"
        if demo_dir.exists():
            shutil.copytree(demo_dir, self.release_path / "demo")
    
    def _copy_scripts(self):
        """Copy utility scripts."""
        print("⚙️ Copying scripts...")
        
        scripts_dir = PROJECT_ROOT / "scripts"
        if scripts_dir.exists():
            # Copy scripts but exclude this release script
            target_scripts = self.release_path / "scripts"
            target_scripts.mkdir(exist_ok=True)
            
            for script_file in scripts_dir.glob("*"):
                if script_file.name != "release.py":
                    if script_file.is_file():
                        shutil.copy2(script_file, target_scripts / script_file.name)
                    elif script_file.is_dir():
                        shutil.copytree(script_file, target_scripts / script_file.name)
    
    def _copy_configuration(self):
        """Copy configuration files."""
        print("⚙️ Copying configuration...")
        
        config_files = [
            ".github",
            "config"
        ]
        
        for config in config_files:
            src = PROJECT_ROOT / config
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, self.release_path / config)
                else:
                    shutil.copy2(src, self.release_path / config)
    
    def _create_release_metadata(self):
        """Create release metadata file."""
        print("📄 Creating release metadata...")
        
        metadata = {
            "name": "Game Telegram",
            "version": self.version,
            "release_type": self.release_type,
            "build_date": datetime.now().isoformat(),
            "build_timestamp": self.timestamp,
            "description": "Interactive Telegram Game Platform",
            "author": "Game Telegram Team",
            "license": "MIT",
            "python_version": "3.8+",
            "components": {
                "services": [
                    "admin-bot",
                    "player-bot", 
                    "game-engine",
                    "session-manager",
                    "user-manager",
                    "analytics-service",
                    "notification-service"
                ],
                "databases": [
                    "PostgreSQL",
                    "Redis"
                ],
                "external_services": [
                    "Telegram Bot API"
                ]
            },
            "features": [
                "Multi-game support (Quiz, Family Feud)",
                "Real-time multiplayer gameplay",
                "Admin management interface",
                "Player statistics and analytics",
                "Session management",
                "Notification system",
                "Comprehensive testing suite",
                "Docker containerization",
                "CI/CD pipeline"
            ],
            "requirements": {
                "system": {
                    "os": "Linux/macOS/Windows",
                    "memory": "2GB RAM minimum",
                    "disk": "1GB free space",
                    "network": "Internet connection required"
                },
                "software": {
                    "docker": "20.10+",
                    "docker-compose": "1.29+",
                    "python": "3.8+ (for development)",
                    "make": "Optional (for development)"
                }
            },
            "installation": {
                "quick_start": "./install.sh",
                "manual": "See docs/deployment/deployment-guide.md",
                "development": "make dev-setup"
            },
            "support": {
                "documentation": "docs/",
                "examples": "demo/",
                "tests": "tests/"
            }
        }
        
        with open(self.release_path / "RELEASE_INFO.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Also create VERSION file
        with open(self.release_path / "VERSION", "w") as f:
            f.write(f"{self.version}\n")
    
    def _create_installation_script(self):
        """Create installation script."""
        print("🚀 Creating installation script...")
        
        install_script = '''#!/bin/bash
# Game Telegram Installation Script
# This script sets up the Game Telegram platform

set -e

echo "🎮 Game Telegram Installation Script"
echo "===================================="

# Check requirements
check_requirements() {
    echo "🔍 Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        echo "   Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        echo "   Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    echo "✅ Requirements check passed"
}

# Setup environment
setup_environment() {
    echo "⚙️ Setting up environment..."
    
    # Copy environment template
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "📝 Created .env file from template"
        echo "⚠️  Please edit .env file with your configuration before starting"
    else
        echo "📝 .env file already exists"
    fi
}

# Setup directories
setup_directories() {
    echo "📁 Setting up directories..."
    
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p logs
    mkdir -p backups
    
    echo "✅ Directories created"
}

# Load demo data
load_demo_data() {
    echo "🎮 Loading demo data..."
    
    if [ -f demo/scripts/load_sample_games.py ]; then
        echo "📊 Demo games will be loaded after first startup"
        echo "   Run: make load-demo-data"
    fi
}

# Main installation
main() {
    echo "Starting installation..."
    
    check_requirements
    setup_environment
    setup_directories
    load_demo_data
    
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your configuration"
    echo "2. Start the platform: docker-compose up -d"
    echo "3. Load demo data: make load-demo-data"
    echo "4. Check status: make status"
    echo ""
    echo "📚 Documentation: docs/"
    echo "🎮 Demo examples: demo/"
    echo "🧪 Run tests: make test"
    echo ""
    echo "Happy gaming! 🎮"
}

# Run installation
main "$@"
'''
        
        install_path = self.release_path / "install.sh"
        with open(install_path, "w") as f:
            f.write(install_script)
        
        # Make executable
        install_path.chmod(0o755)
    
    def _create_archives(self):
        """Create release archives."""
        print("📦 Creating archives...")
        
        # Create tar.gz archive
        tar_path = RELEASE_DIR / f"{self.release_name}.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(self.release_path, arcname=self.release_name)
        
        # Create zip archive
        zip_path = RELEASE_DIR / f"{self.release_name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.release_path):
                for file in files:
                    file_path = Path(root) / file
                    arc_path = Path(self.release_name) / file_path.relative_to(self.release_path)
                    zipf.write(file_path, arc_path)
        
        print(f"📦 Created {tar_path.name}")
        print(f"📦 Created {zip_path.name}")
    
    def _create_checksums(self):
        """Create checksum files."""
        print("🔐 Creating checksums...")
        
        import hashlib
        
        checksum_file = RELEASE_DIR / f"{self.release_name}.checksums.txt"
        
        archives = [
            f"{self.release_name}.tar.gz",
            f"{self.release_name}.zip"
        ]
        
        with open(checksum_file, "w") as f:
            f.write(f"# Checksums for {self.release_name}\n")
            f.write(f"# Generated on {datetime.now().isoformat()}\n\n")
            
            for archive in archives:
                archive_path = RELEASE_DIR / archive
                if archive_path.exists():
                    # Calculate SHA256
                    sha256_hash = hashlib.sha256()
                    with open(archive_path, "rb") as af:
                        for chunk in iter(lambda: af.read(4096), b""):
                            sha256_hash.update(chunk)
                    
                    f.write(f"SHA256({archive}) = {sha256_hash.hexdigest()}\n")
        
        print(f"🔐 Created {checksum_file.name}")

def get_version() -> str:
    """Get version from VERSION file or prompt user."""
    version_file = PROJECT_ROOT / "VERSION"
    
    if version_file.exists():
        with open(version_file) as f:
            return f.read().strip()
    
    # Default version if file doesn't exist
    return "1.0.0"

def update_version(version: str):
    """Update VERSION file."""
    version_file = PROJECT_ROOT / "VERSION"
    with open(version_file, "w") as f:
        f.write(f"{version}\n")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create Game Telegram release package")
    parser.add_argument(
        "--version", 
        help="Release version (e.g., 1.0.0)",
        default=None
    )
    parser.add_argument(
        "--type",
        choices=["stable", "beta", "alpha", "rc"],
        default="stable",
        help="Release type"
    )
    parser.add_argument(
        "--update-version",
        action="store_true",
        help="Update VERSION file with new version"
    )
    
    args = parser.parse_args()
    
    # Determine version
    if args.version:
        version = args.version
        if args.update_version:
            update_version(version)
    else:
        version = get_version()
    
    print(f"🚀 Game Telegram Release Manager")
    print(f"Version: {version}")
    print(f"Type: {args.type}")
    print("=" * 50)
    
    # Create release
    release_manager = ReleaseManager(version, args.type)
    success = release_manager.create_release()
    
    if success:
        print("\n🎉 Release packaging completed successfully!")
        print(f"📁 Release directory: {release_manager.release_path}")
        print(f"📦 Archives available in: {RELEASE_DIR}")
        sys.exit(0)
    else:
        print("\n❌ Release packaging failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()