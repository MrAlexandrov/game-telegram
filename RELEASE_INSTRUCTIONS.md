# Release Instructions

This document provides instructions for creating and managing releases of the Game Telegram project.

## Release System Overview

The project includes a comprehensive release management system that packages all components into distributable archives.

### Release Components

- **Source Code**: All microservices and shared components
- **Tests**: Complete test suite with 2000+ test cases
- **Documentation**: User guides, API docs, deployment guides
- **Demo Data**: Sample games and examples
- **Scripts**: Installation, verification, and utility scripts
- **Configuration**: Docker, CI/CD, and environment setup

## Creating a Release

### Prerequisites

- Python 3.8+
- All project files in place
- VERSION file with current version

### Quick Release Creation

```bash
# Make scripts executable
chmod +x scripts/create_first_release.sh scripts/release.py

# Create the first release (1.0.0)
./scripts/create_first_release.sh
```

### Manual Release Creation

```bash
# Create release using Python script
python3 scripts/release.py --version 1.0.0 --type stable

# Or use Makefile commands
make release                    # Create release with current version
make release-version           # Show current version
make release-patch            # Create patch release (x.y.z+1)
make release-minor            # Create minor release (x.y+1.0)
make release-major            # Create major release (x+1.0.0)
make release-beta             # Create beta release
make release-clean            # Clean release artifacts
```

## Release Types

- **stable**: Production-ready release
- **beta**: Pre-release for testing
- **alpha**: Early development release
- **rc**: Release candidate

## Release Artifacts

After creating a release, you'll find:

```
releases/
├── game-telegram-1.0.0/              # Complete release directory
├── game-telegram-1.0.0.tar.gz        # Compressed archive (Linux/macOS)
├── game-telegram-1.0.0.zip           # Compressed archive (Windows)
└── game-telegram-1.0.0.checksums.txt # SHA256 checksums
```

## Release Directory Structure

```
game-telegram-1.0.0/
├── install.sh                 # Installation script
├── README.md                  # Project overview
├── LICENSE                    # MIT license
├── VERSION                    # Version file
├── CHANGELOG.md               # Release notes
├── RELEASE_INFO.json          # Release metadata
├── docker-compose.yml         # Main compose file
├── docker-compose.prod.yml    # Production compose
├── docker-compose.test.yml    # Testing compose
├── .env.example               # Environment template
├── Makefile                   # Development commands
├── pytest.ini                # Test configuration
├── services/                  # All microservices
│   ├── admin-bot/
│   ├── player-bot/
│   ├── game-engine/
│   ├── session-manager/
│   ├── user-manager/
│   ├── analytics-service/
│   └── notification-service/
├── shared/                    # Shared components
├── tests/                     # Complete test suite
├── docs/                      # Documentation
├── demo/                      # Demo data and examples
├── scripts/                   # Utility scripts
└── .github/                   # CI/CD configuration
```

## Installation for End Users

Users can install the release by:

```bash
# Extract release
tar -xzf game-telegram-1.0.0.tar.gz
cd game-telegram-1.0.0

# Run installation script
./install.sh

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start the platform
docker-compose up -d

# Load demo data
make load-demo-data
```

## Version Management

### Version Format

The project uses semantic versioning (SemVer): `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Updating Versions

```bash
# Update VERSION file manually
echo "1.1.0" > VERSION

# Or use release commands that auto-increment
make release-patch    # 1.0.0 → 1.0.1
make release-minor    # 1.0.0 → 1.1.0
make release-major    # 1.0.0 → 2.0.0
```

## Release Checklist

Before creating a release:

- [ ] All tests pass (`make test`)
- [ ] Documentation is up to date
- [ ] CHANGELOG.md is updated
- [ ] VERSION file contains correct version
- [ ] Demo data is current
- [ ] CI/CD pipeline passes
- [ ] Security scan passes
- [ ] Performance tests pass

## Release Metadata

Each release includes `RELEASE_INFO.json` with:

```json
{
  "name": "Game Telegram",
  "version": "1.0.0",
  "release_type": "stable",
  "build_date": "2024-12-20T10:00:00Z",
  "components": ["admin-bot", "player-bot", "..."],
  "features": ["Multi-game support", "..."],
  "requirements": {
    "system": {"os": "Linux/macOS/Windows", "memory": "2GB RAM"},
    "software": {"docker": "20.10+", "docker-compose": "1.29+"}
  }
}
```

## Distribution

### Internal Distribution

- Store releases in `releases/` directory
- Share archives via file sharing systems
- Document release notes in CHANGELOG.md

### External Distribution

- Upload to GitHub Releases
- Publish to package repositories
- Update documentation websites
- Notify users of new releases

## Troubleshooting

### Common Issues

1. **Missing dependencies**: Ensure Python 3.8+ is installed
2. **Permission errors**: Make scripts executable with `chmod +x`
3. **Disk space**: Releases can be 100MB+, ensure sufficient space
4. **Path issues**: Run scripts from project root directory

### Verification

```bash
# Verify release contents
ls -la releases/game-telegram-1.0.0/

# Check checksums
sha256sum -c releases/game-telegram-1.0.0.checksums.txt

# Test installation
cd releases/game-telegram-1.0.0/
./install.sh
```

## Support

For release-related issues:

1. Check this documentation
2. Review CHANGELOG.md for known issues
3. Run system verification: `make verify`
4. Check logs: `make logs`

## Future Enhancements

Planned improvements to the release system:

- Automated GitHub Releases integration
- Docker image publishing
- Package repository publishing
- Release signing and verification
- Automated testing of release packages
- Multi-platform builds