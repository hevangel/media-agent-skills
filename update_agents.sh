#!/usr/bin/env bash
# Update AI CLI Tools
# Bash equivalent of update_agents.ps1

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=== Updating AI CLI Tools ===${NC}"
echo ""

# Update GitHub Copilot CLI
echo -e "${YELLOW}Updating GitHub Copilot CLI...${NC}"
if npm update -g @githubnext/github-copilot-cli 2>/dev/null; then
    echo -e "${GREEN}✓ GitHub Copilot CLI updated${NC}"
else
    echo -e "${RED}! Error updating GitHub Copilot CLI${NC}"
fi
echo ""

# Update Cursor Agent CLI
echo -e "${YELLOW}Updating Cursor Agent CLI...${NC}"
if command -v agent &>/dev/null && agent update 2>/dev/null; then
    echo -e "${GREEN}✓ Cursor Agent CLI updated${NC}"
else
    echo -e "${RED}! Error updating Cursor Agent CLI (not installed or update failed)${NC}"
fi
echo ""

# Update Claude Code CLI
echo -e "${YELLOW}Updating Claude Code CLI...${NC}"
if command -v claude &>/dev/null && claude update 2>/dev/null; then
    echo -e "${GREEN}✓ Claude Code CLI updated${NC}"
else
    echo -e "${RED}! Error updating Claude Code CLI (not installed or update failed)${NC}"
fi
echo ""

# Update OpenAI Codex CLI
echo -e "${YELLOW}Updating OpenAI Codex CLI...${NC}"
if npm update -g @openai/codex-cli 2>/dev/null; then
    echo -e "${GREEN}✓ OpenAI Codex CLI updated${NC}"
else
    echo -e "${RED}! Error updating OpenAI Codex CLI${NC}"
fi
echo ""

# Update Google Gemini CLI
echo -e "${YELLOW}Updating Google Gemini CLI...${NC}"
if npm update -g @google/gemini-cli 2>/dev/null; then
    echo -e "${GREEN}✓ Google Gemini CLI updated${NC}"
else
    echo -e "${RED}! Error updating Google Gemini CLI${NC}"
fi
echo ""

echo -e "${CYAN}=== Update Complete ===${NC}"
echo -e "${YELLOW}Please restart your terminal for changes to take effect.${NC}"
