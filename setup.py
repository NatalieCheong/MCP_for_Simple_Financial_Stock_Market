#!/usr/bin/env python3
"""
Setup script for Financial MCP Project
This script helps you set up the project environment and dependencies.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(command, check=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_dependencies():
    """Check if required system dependencies are installed."""
    print("🔍 Checking system dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} found")
    
    # Check uv
    success, _, _ = run_command("uv --version", check=False)
    if not success:
        print("❌ uv not found. Please install uv: https://docs.astral.sh/uv/getting-started/installation/")
        return False
    print("✅ uv found")
    
    # Check Node.js (for MCP inspector and filesystem server)
    success, _, _ = run_command("node --version", check=False)
    if not success:
        print("⚠️  Node.js not found. MCP inspector and filesystem server won't work")
        print("   Install Node.js from: https://nodejs.org/")
    else:
        print("✅ Node.js found")
    
    return True

def setup_project():
    """Set up the project environment."""
    print("\n🚀 Setting up Financial MCP Project...")
    
    # Create virtual environment
    print("📦 Creating virtual environment...")
    success, stdout, stderr = run_command("uv venv")
    if not success:
        print(f"❌ Failed to create virtual environment: {stderr}")
        return False
    print("✅ Virtual environment created")
    
    # Install dependencies
    print("📥 Installing dependencies...")
    dependencies = [
        "mcp>=1.8.0",
        "yfinance>=0.2.18", 
        "anthropic>=0.57.1",
        "python-dotenv>=1.1.0",
        "nest-asyncio>=1.6.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0"
    ]
    
    for dep in dependencies:
        print(f"   Installing {dep}...")
        success, _, stderr = run_command(f"uv add {dep}")
        if not success:
            print(f"❌ Failed to install {dep}: {stderr}")
            return False
    
    print("✅ All dependencies installed")
    
    # Create directories
    print("📁 Creating directories...")
    os.makedirs("financial_data", exist_ok=True)
    print("✅ Directories created")
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        print("🔐 Creating .env file...")
        with open(".env", "w") as f:
            f.write("# Anthropic API Key for Claude\n")
            f.write("ANTHROPIC_API_KEY=your_anthropic_api_key_here\n")
            f.write("\n# Optional: Logging level\n")
            f.write("LOG_LEVEL=INFO\n")
        print("✅ .env file created - please add your Anthropic API key")
    
    return True

def test_setup():
    """Test the setup by running basic checks."""
    print("\n🧪 Testing setup...")
    
    # Test yfinance import
    try:
        import yfinance as yf
        print("✅ yfinance import successful")
    except ImportError as e:
        print(f"❌ yfinance import failed: {e}")
        return False
    
    # Test MCP import
    try:
        from mcp.server.fastmcp import FastMCP
        print("✅ MCP import successful")
    except ImportError as e:
        print(f"❌ MCP import failed: {e}")
        return False
    
    # Test basic yfinance functionality
    try:
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        if 'currentPrice' in info or 'regularMarketPrice' in info:
            print("✅ yfinance API test successful")
        else:
            print("⚠️  yfinance API test returned no price data")
    except Exception as e:
        print(f"⚠️  yfinance API test failed: {e}")
    
    return True

def print_next_steps():
    """Print instructions for next steps."""
    print("\n" + "="*60)
    print("🎉 Setup Complete!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Add your Anthropic API key to .env file:")
    print("   ANTHROPIC_API_KEY=your_actual_api_key_here")
    print("\n2. Activate the virtual environment:")
    print("   source .venv/bin/activate  # Linux/Mac")
    print("   .venv\\Scripts\\activate     # Windows")
    print("\n3. Test the MCP server:")
    print("   npx @modelcontextprotocol/inspector uv run financial_server.py")
    print("\n4. Run the financial chatbot:")
    print("   uv run financial_chatbot.py")
    print("\n5. Try some example queries:")
    print("   - What's the current price of Apple stock?")
    print("   - Compare AAPL, GOOGL, and MSFT by market cap")
    print("   - @portfolios")
    print("   - /prompts")
    print("\n📚 See README.md for detailed usage instructions")
    print("\n💡 Tip: Use 'quit' to exit the chatbot")

def main():
    """Main setup function."""
    print("💰 Financial MCP Project Setup")
    print("="*50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Setup failed - missing dependencies")
        sys.exit(1)
    
    # Setup project
    if not setup_project():
        print("\n❌ Setup failed - project setup error")
        sys.exit(1)
    
    # Test setup
    if not test_setup():
        print("\n⚠️  Setup completed with warnings")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
