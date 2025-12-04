#!/bin/bash

# ============================================================================
# Codespaces Post-Create Setup
# ============================================================================

echo "🚀 Setting up Adaptheon development environment..."

# Configure Git
git config --global user.name "Ishabdullah"
git config --global user.email "ismail.t.abdullah@gmail.com"
git config --global init.defaultBranch dev

# Install Claude Code
echo "📦 Installing Claude Code..."
npm install -g @anthropic-ai/claude-code

# Create Claude Code settings
mkdir -p ~/.claude
cat > ~/.claude/settings.json << 'SETTINGS'
{
  "autoUpdate": true,
  "defaultModel": "claude-sonnet-4-5-20250929",
  "theme": "dark"
}
SETTINGS

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Install project dependencies if package.json exists
if [ -f "package.json" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

echo "✅ Setup complete!"
echo ""
echo "To use Claude Code, run: claude"
echo "You'll need to authenticate with your Claude Pro account on first run."
