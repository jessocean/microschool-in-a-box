# Claude Code Windows Development Setup

## Issues We're Experiencing
- `/usr/bin/bash: Files\Git\bin\bash.exe: No such file or directory`
- Unable to run npm, pnpm, or package managers via Claude's Bash tool
- PowerShell commands failing with path/redirection issues

## Solutions

### 1. Fix Git Bash Path Issues

The main issue is that Claude Code can't find Git Bash. Try these solutions in order:

**Option A: Set Git Bash Path Environment Variable**
```powershell
# Add to your system environment variables:
CLAUDE_CODE_GIT_BASH_PATH=C:\Program Files\Git\bin\bash.exe
```

**Option B: Alternative Git Bash Locations**
If Option A doesn't work, try setting the path to one of these:
- `C:\Program Files (x86)\Git\bin\bash.exe`
- `C:\Users\%USERNAME%\AppData\Local\Programs\Git\bin\bash.exe`
- `C:\Git\bin\bash.exe`

**Option C: Use Windows Git Bash directly**
```cmd
# Find your Git Bash location:
where bash
# Then set CLAUDE_CODE_GIT_BASH_PATH to that location
```

### 2. Package Manager Solutions

**For npm issues:**
```cmd
# Refresh PATH
refreshenv
# Or restart your terminal and try:
npm --version
```

**For pnpm issues:**
```cmd
# Install pnpm via npm (most reliable on Windows):
npm install -g pnpm

# Or via Corepack (Node.js 16+):
corepack enable
corepack prepare pnpm@latest --activate
```

**For Supabase CLI:**
```powershell
# Use Chocolatey (if installed):
choco install supabase

# Or use Scoop:
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase

# Or manual download from GitHub releases
```

### 3. Alternative Approaches When Shell Fails

**Manual Package Installation:**
When Claude can't run commands, you can:
1. Claude will modify `package.json` to add dependencies
2. You manually run `npm install` or `pnpm install` in your terminal
3. Claude continues with the rest of the setup

**SQL Migrations:**
When Supabase CLI fails:
1. Claude will provide the SQL migration content
2. You copy-paste it into Supabase Dashboard → SQL Editor
3. Run the migration manually

### 4. Environment Setup Commands

**Run these in PowerShell as Administrator:**

```powershell
# Check current PATH
$env:PATH -split ';' | Where-Object { $_ -match "git|node|npm" }

# Add Git to PATH if missing
$env:PATH += ";C:\Program Files\Git\bin"

# Verify installations
git --version
node --version
npm --version
pnpm --version
```

### 5. WSL2 Alternative (Nuclear Option)

If nothing else works:
```powershell
# Install WSL2
wsl --install

# Install Ubuntu
wsl --install -d Ubuntu

# In WSL2, install everything:
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g pnpm
npx supabase --version
```

## Testing the Fix

After applying any solution, test with:
```bash
# Test in Claude Code:
echo "Testing shell access"
node --version
npm --version
pnpm --version
```

## Troubleshooting Checklist

1. **Restart VS Code/Terminal** after environment changes
2. **Check PATH variables** include Git, Node, npm locations  
3. **Run as Administrator** if permission issues
4. **Use forward slashes** in paths when possible: `/c/Users/...`
5. **Escape spaces** in paths: `"C:\Program Files\Git\bin\bash.exe"`

## Current Working Directory

When Claude runs commands, it should be in: `C:\Users\jessi\dev`

For project-specific commands:
- Frontend: `C:\Users\jessi\dev\aimarriagebot\frontend`
- Root: `C:\Users\jessi\dev\aimarriagebot`

## Best Practices

- **Always use full paths** when commands fail
- **Prefer PowerShell over cmd** for better Unicode support
- **Use pnpm over npm** for faster installs and better Windows compatibility
- **Install global tools via package managers** rather than manual downloads

## Emergency Manual Commands

If Claude can't run these commands, run them manually:

```bash
# In aimarriagebot/frontend:
pnpm install

# In aimarriagebot root:
npm install -g supabase
supabase db push

# Alternative Supabase install:
npm install -g @supabase/supabase-js
```