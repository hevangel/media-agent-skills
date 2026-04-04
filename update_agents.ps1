# PowerShell script to update AI CLI tools
# Run as Administrator if needed

Write-Host "=== Updating AI CLI Tools ===" -ForegroundColor Cyan
Write-Host ""

# Update GitHub Copilot CLI
Write-Host "Updating GitHub Copilot CLI..." -ForegroundColor Yellow
try {
    # Update via npm
    npm update -g @githubnext/github-copilot-cli
    Write-Host "✓ GitHub Copilot CLI updated" -ForegroundColor Green
} catch {
    Write-Host "! Error updating GitHub Copilot CLI: $_" -ForegroundColor Red
}
Write-Host ""

# Update Cursor Agent CLI
Write-Host "Updating Cursor Agent CLI..." -ForegroundColor Yellow
try {
    # Update using agent update command
    agent update
    Write-Host "✓ Cursor Agent CLI updated" -ForegroundColor Green
} catch {
    Write-Host "! Error updating Cursor Agent CLI: $_" -ForegroundColor Red
}
Write-Host ""

# Update Claude Code CLI
Write-Host "Updating Claude Code CLI..." -ForegroundColor Yellow
try {
    # Update using claude update command
    claude update
    Write-Host "✓ Claude Code CLI updated" -ForegroundColor Green
} catch {
    Write-Host "! Error updating Claude Code CLI: $_" -ForegroundColor Red
}
Write-Host ""

# Update OpenAI Codex CLI
Write-Host "Updating OpenAI Codex CLI..." -ForegroundColor Yellow
try {
    # Update via npm
    npm update -g @openai/codex-cli
    Write-Host "✓ OpenAI Codex CLI updated" -ForegroundColor Green
} catch {
    Write-Host "! Error updating OpenAI Codex CLI: $_" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "=== Update Complete ===" -ForegroundColor Cyan
Write-Host "Please restart your terminal for changes to take effect." -ForegroundColor Yellow

# Update Google Gemini CLI
Write-Host "Updating Google Gemini CLI..." -ForegroundColor Yellow
try {
    # Update via npm
    npm update -g @google/gemini-cli
    Write-Host "✓ Google Gemini CLI updated" -ForegroundColor Green
} catch {
    Write-Host "! Error updating Google Gemini CLI: $_" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "=== Update Complete ===" -ForegroundColor Cyan
Write-Host "Please restart your terminal for changes to take effect." -ForegroundColor Yellow
