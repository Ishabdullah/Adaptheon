# Adaptheon - Codespaces Setup

This configuration sets up a complete development environment for Adaptheon in GitHub Codespaces.

## What's Included

- **Python 3.11** - Full Python development environment
- **Node.js 20** - For JavaScript/TypeScript development
- **Claude Code** - AI-powered coding assistant
- **Git** - Version control
- **GitHub CLI** - GitHub integration

## Getting Started in Codespaces

1. Go to your Adaptheon repository on GitHub
2. Click the green "Code" button
3. Select "Codespaces" tab
4. Click "Create codespace on dev"
5. Wait for the environment to build (~2-3 minutes)

## First Time Setup in Codespace

After the Codespace loads:

1. Open a new terminal
2. Run: `claude`
3. Select: "1. Claude account with subscription"
4. Authenticate with your Claude Pro account
5. Start coding!

## Useful Commands

- `claude` - Start Claude Code
- `/status` - Check Claude usage
- `git status` - Check repository status
- `python --version` - Check Python version
- `node --version` - Check Node.js version

## Port Forwarding

The following ports are automatically forwarded:
- 3000 - Frontend
- 5000 - Backend API
- 8000 - HTTP Server
- 8080 - Alt HTTP Server
- 8501 - Streamlit

## Syncing with Termux

Your Codespace is connected to the same GitHub repository as your Termux setup.

**Workflow:**
1. Make changes in Codespace
2. Commit and push to `dev` branch
3. Pull changes in Termux with: `git pull origin dev`

Or vice versa!

## Free Tier Limits

GitHub Free accounts get:
- 120 core hours/month
- 15 GB storage

That's about 60 hours/month of coding on a 2-core machine.

## Tips

- Use Codespaces for heavy ML training
- Use Termux for quick edits and prototyping
- Always work on the `dev` branch
- Commit frequently!
