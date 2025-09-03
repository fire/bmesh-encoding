#!/usr/bin/env python3
"""
Development setup script for EXT_bmesh_encoding.
Configures the development environment and provides utility functions.
"""

import os
import sys
import subprocess
from pathlib import Path


def setup_environment():
    """Set up the development environment."""
    print("🔧 Setting up EXT_bmesh_encoding development environment...")

    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Load environment variables
    load_env_file()

    # Set up Python path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    print("✅ Development environment configured")
    return True


def load_env_file():
    """Load environment variables from .env file."""
    env_file = Path('.env')
    if env_file.exists():
        print("📄 Loading environment variables from .env")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
                        print(f"   {key}={value}")
    else:
        print("⚠️  No .env file found - using default settings")


def check_blender_installation():
    """Check if Blender is installed and accessible."""
    print("\n🔍 Checking Blender installation...")

    blender_path = os.environ.get('BLENDER_PATH', '/usr/bin/blender')

    try:
        result = subprocess.run([blender_path, '--version'],
                              capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ Blender found: {version_line}")
            print(f"   Path: {blender_path}")
            return True
        else:
            print(f"❌ Blender not found at {blender_path}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"❌ Blender not found at {blender_path}")
        return False


def check_uv_installation():
    """Check if uv is installed."""
    print("\n🔍 Checking uv installation...")

    try:
        result = subprocess.run(['uv', '--version'],
                              capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            version_line = result.stdout.strip()
            print(f"✅ uv found: {version_line}")
            return True
        else:
            print("❌ uv not found")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ uv not found")
        return False


def install_dependencies():
    """Install project dependencies using uv."""
    print("\n📦 Installing dependencies...")

    try:
        result = subprocess.run(['uv', 'sync'], timeout=60)

        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print("❌ Failed to install dependencies")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Failed to run uv sync")
        return False


def run_tests():
    """Run the test suite."""
    print("\n🧪 Running tests...")

    test_commands = [
        ['uv', 'run', 'python', 'test_addon_load.py'],
        ['uv', 'run', 'python', 'test_gltf_validation_simple.py'],
        ['uv', 'run', 'python', '-m', 'pytest', 'test_extension_hooks.py', '-v']
    ]

    # Add Blender-based tests if Blender is available
    blender_path = os.environ.get('BLENDER_PATH', '/usr/bin/blender')
    if os.path.exists(blender_path):
        test_commands.extend([
            [blender_path, '--background', '--python', 'test_topology_validation.py'],
            [blender_path, '--background', '--python', 'test_blender_integration.py']
        ])

    results = []
    for cmd in test_commands:
        print(f"\n🔄 Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, timeout=60)  # Increased timeout for Blender tests
            success = result.returncode == 0
            results.append(success)
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   Result: {status}")
        except subprocess.TimeoutExpired:
            print("   Result: ❌ TIMEOUT")
            results.append(False)

    overall_success = all(results)
    print(f"\n📊 Test Results: {'✅ ALL PASSED' if overall_success else '❌ SOME FAILED'}")

    if not overall_success:
        print("\n🔍 Test Failure Analysis:")
        print("   • If topology tests fail: EXT_bmesh_encoding is not preserving quads/ngons")
        print("   • If extension validation fails: Addon hooks are not being called")
        print("   • If Blender tests timeout: Blender installation or path issues")

    return overall_success


def show_usage():
    """Show usage information."""
    print("""
EXT_bmesh_encoding Development Setup
====================================

Available commands:
  python setup_dev.py setup      - Set up development environment
  python setup_dev.py check      - Check system requirements
  python setup_dev.py install    - Install dependencies
  python setup_dev.py test       - Run test suite
  python setup_dev.py all        - Run all setup steps

Environment variables (.env):
  BLENDER_PATH     - Path to Blender executable
  BLENDER_VERSION  - Blender version
  DEBUG           - Enable debug logging
  LOG_LEVEL       - Logging level

For Blender testing:
  blender --background --python test_quad_roundtrip.py
""")


def main():
    """Main setup function."""
    if len(sys.argv) < 2:
        show_usage()
        return

    command = sys.argv[1]

    if command == 'setup':
        setup_environment()
    elif command == 'check':
        setup_environment()
        check_blender_installation()
        check_uv_installation()
    elif command == 'install':
        setup_environment()
        install_dependencies()
    elif command == 'test':
        setup_environment()
        run_tests()
    elif command == 'all':
        print("🚀 Running complete setup...")
        setup_environment()
        check_blender_installation()
        check_uv_installation()
        install_dependencies()
        run_tests()
        print("\n🎉 Setup complete!")
    else:
        print(f"❌ Unknown command: {command}")
        show_usage()


if __name__ == "__main__":
    main()
