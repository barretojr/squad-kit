[CmdletBinding()]
param(
    [string]$TargetProject,
    [switch]$Global
)

# Installs the Squad for Antigravity (.agents/ in a project, or ~/.gemini/config globally).
$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceDir = Join-Path $ScriptDir 'squad-kit'
$Kinds = @('agents', 'rules', 'skills', 'commands', 'mcp')

if (-not (Test-Path -LiteralPath $SourceDir -PathType Container)) {
    throw "Source folder 'squad-kit' not found in: $ScriptDir"
}

function Copy-SquadTo {
    param([string]$DestinationRoot)
    foreach ($Kind in $Kinds) {
        $From = Join-Path $SourceDir $Kind
        if (Test-Path -LiteralPath $From -PathType Container) {
            $To = Join-Path $DestinationRoot $Kind
            New-Item -ItemType Directory -Path $To -Force | Out-Null
            Copy-Item -Path (Join-Path $From '*') -Destination $To -Recurse -Force
        }
    }
    # The squad skill reads its rules from references/rules.md
    Copy-Item -LiteralPath (Join-Path $SourceDir 'rules\squad-context.md') -Destination (Join-Path $DestinationRoot 'skills\squad\references\rules.md') -Force
}

function Copy-ToGlobalConfig {
    $ConfigDir = Join-Path $HOME '.gemini\config'
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
    Copy-SquadTo -DestinationRoot $ConfigDir
    $GlobalSkillsDir = Join-Path $HOME '.gemini\antigravity-cli\skills'
    New-Item -ItemType Directory -Path $GlobalSkillsDir -Force | Out-Null
    Copy-Item -Path (Join-Path $SourceDir 'skills\*') -Destination $GlobalSkillsDir -Recurse -Force
    Copy-Item -LiteralPath (Join-Path $SourceDir 'rules\squad-context.md') -Destination (Join-Path $GlobalSkillsDir 'squad\references\rules.md') -Force
    Write-Host "Squad and skills installed globally in $ConfigDir and $GlobalSkillsDir." -ForegroundColor Green
    Write-Host "MCP server: python `"$(Join-Path $ConfigDir 'mcp\server.py')`" (stdio)"
}

if ($Global) {
    Copy-ToGlobalConfig
    exit 0
}

if ([string]::IsNullOrWhiteSpace($TargetProject)) {
    Write-Host '1) Install into the current folder'
    Write-Host '2) Enter another project'
    Write-Host '3) Install globally'
    Write-Host 'q) Cancel'
    $Choice = Read-Host 'Option'
    switch ($Choice) {
        '1' { $TargetProject = (Get-Location).Path }
        '2' { $TargetProject = Read-Host 'Project root' }
        '3' { Copy-ToGlobalConfig; exit 0 }
        default { Write-Host 'Cancelled.'; exit 0 }
    }
}

if (-not (Test-Path -LiteralPath $TargetProject -PathType Container)) {
    throw "Project folder not found: $TargetProject"
}
$DestDir = Join-Path $TargetProject '.agents'
New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
Copy-SquadTo -DestinationRoot $DestDir

# Make sure .squad/ is in the project's .gitignore
$GitIgnorePath = Join-Path $TargetProject '.gitignore'
$GitIgnoreContent = if (Test-Path -LiteralPath $GitIgnorePath) { Get-Content -LiteralPath $GitIgnorePath -Raw } else { '' }
if ($GitIgnoreContent -notmatch '(?m)^\.squad/?\s*$') {
    Add-Content -LiteralPath $GitIgnorePath -Value "`n# Squad artifacts`n.squad/" -Encoding utf8
    Write-Host "Added .squad/ to $GitIgnorePath" -ForegroundColor Cyan
}

Write-Host "Squad installed in the workspace: $DestDir" -ForegroundColor Green
Write-Host 'Reopen or reload Antigravity and run /squad.'
Write-Host "MCP server: python `"$(Join-Path $DestDir 'mcp\server.py')`" (stdio)"
