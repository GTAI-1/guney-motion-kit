# capcut-story-film doctor and installer for Windows 10/11.  UNTESTED: written on a Mac, never run on Windows yet.
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1              check only (default), changes nothing
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -DryRun      print what -Install would do
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Install     show the list, ask once, install the missing pieces
#   add -Yes to skip the question (only after the user said yes in chat); -NoRender skips the HyperFrames test render
# Uses winget (built into Windows 10/11). Never deletes anything. Writes .\capcut-story-film-setup.log on install.
# See references/windows-notes.md for what is known and unknown about CapCut on Windows.
param([switch]$Install, [switch]$DryRun, [switch]$Yes, [switch]$NoRender)
$ErrorActionPreference = 'Continue'
$Skill = Split-Path -Parent $PSScriptRoot
$Cfg = Join-Path $Skill 'skill.config.json'
$conf = if (Test-Path $Cfg) { Get-Content $Cfg -Raw | ConvertFrom-Json } else { $null }
$FlowRepo = if ($env:FLOW_MCP_REPO) { $env:FLOW_MCP_REPO } elseif ($conf) { $conf.flow_mcp_repo } else { '' }
$FlowDir = if ($env:FLOW_MCP_DIR) { $env:FLOW_MCP_DIR } else { Join-Path $HOME 'flow-mcp' }
$HF = if ($env:HF_VERSION) { $env:HF_VERSION } else { '0.7.109' }
$Model = if ($env:WHISPER_MODEL) { $env:WHISPER_MODEL } else { Join-Path $HOME '.cache\whisper-models\ggml-small.en.bin' }
$ModelUrl = 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin'
$WhisperDir = Join-Path $env:LOCALAPPDATA 'whisper.cpp'
$Log = Join-Path (Get-Location) 'capcut-story-film-setup.log'
$rows = New-Object System.Collections.ArrayList; $todo = New-Object System.Collections.ArrayList; $fails = 0
function Row($item, $status, $detail) { [void]$rows.Add([pscustomobject]@{ ITEM = $item; STATUS = $status; DETAIL = $detail }); if ($status -eq 'MISSING') { $script:fails++ } }
function Todo($desc, $cmd) { [void]$todo.Add([pscustomobject]@{ D = $desc; C = $cmd }) }
function Has($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }

Row 'Windows' 'OK' ([Environment]::OSVersion.VersionString)
if (Has 'winget') { Row 'winget' 'OK' 'Windows package manager' } else { Row 'winget' 'MISSING' 'install "App Installer" from the Microsoft Store (you)' }

if ((Has 'node') -and ([int]((node -p "process.versions.node.split('.')[0]") 2>$null) -ge 22)) { Row 'Node.js 22+' 'OK' (node -v) }
else { Row 'Node.js 22+' 'MISSING' 'HyperFrames, the score engine, the Flow MCP'; Todo 'Node.js LTS' 'winget install -e --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements' }

$py = if (Has 'py') { 'py' } elseif (Has 'python') { 'python' } else { $null }
if ($py -and ((& $py --version 2>&1) -match 'Python 3')) {
  Row 'Python 3' 'OK' (& $py --version 2>&1)
  & $py -c "import PIL, numpy" 2>$null
  if ($LASTEXITCODE -eq 0) { Row 'Pillow + numpy' 'OK' 'python modules' } else { Row 'Pillow + numpy' 'MISSING' 'picture and audio maths'; Todo 'Pillow and numpy' "$py -m pip install --user pillow numpy" }
} else {
  Row 'Python 3' 'MISSING' 'the planning scripts'; Todo 'Python 3' 'winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements'
  Row 'Pillow + numpy' 'MISSING' 'after Python'; Todo 'Pillow and numpy' 'py -m pip install --user pillow numpy'
}

if ((Has 'ffmpeg') -and (Has 'ffprobe')) { Row 'ffmpeg + ffprobe' 'OK' ((ffmpeg -version | Select-Object -First 1) -split ' ')[2] }
else { Row 'ffmpeg + ffprobe' 'MISSING' 'audio, video, overlays (ProRes 4444 on Windows)'; Todo 'ffmpeg' 'winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements' }

if (Has 'whisper-cli') { Row 'whisper.cpp (whisper-cli)' 'OK' 'word timing from the voice' }
else {
  Row 'whisper.cpp (whisper-cli)' 'MISSING' 'exact word timing (fallback without it: slower, less exact)'
  Todo "whisper.cpp (official release zip from GitHub into $WhisperDir, added to your PATH)" ("`$r = Invoke-RestMethod https://api.github.com/repos/ggml-org/whisper.cpp/releases/latest; `$a = `$r.assets | Where-Object name -eq 'whisper-bin-x64.zip'; " +
    "New-Item -ItemType Directory -Force '$WhisperDir' | Out-Null; Invoke-WebRequest `$a.browser_download_url -OutFile '$WhisperDir\w.zip'; Expand-Archive '$WhisperDir\w.zip' '$WhisperDir' -Force; " +
    "`$bin = (Get-ChildItem '$WhisperDir' -Recurse -Filter whisper-cli.exe | Select-Object -First 1).DirectoryName; [Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path','User') + ';' + `$bin, 'User')")
}
if (Test-Path $Model) { Row 'Whisper model small.en' 'OK' ('{0:N0} MB' -f ((Get-Item $Model).Length / 1MB)) }
else { Row 'Whisper model small.en' 'MISSING' '466 MB speech model'; Todo 'Whisper model ggml-small.en.bin (466 MB from Hugging Face)' "New-Item -ItemType Directory -Force '$(Split-Path $Model)' | Out-Null; Invoke-WebRequest '$ModelUrl' -OutFile '$Model.part'; Move-Item '$Model.part' '$Model'" }

$ccExe = @("$env:LOCALAPPDATA\CapCut\Apps\CapCut.exe", "$env:ProgramFiles\CapCut\CapCut.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $ccExe) { $ccExe = Get-ChildItem "$env:LOCALAPPDATA\CapCut\Apps" -Recurse -Filter CapCut.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName }
if ($ccExe) { $v = (Get-Item $ccExe).VersionInfo.ProductVersion; Row 'CapCut desktop' $(if ($v -like '9.1*') { 'OK' } else { 'WARN' }) "$v (tested with 9.1 on Mac; Windows untested)" }
else { Row 'CapCut desktop' 'MISSING' 'install it yourself from capcut.com (free), open it once, quit it' }
$drafts = if ($env:CAPCUT_DRAFTS) { $env:CAPCUT_DRAFTS } else { Join-Path $env:LOCALAPPDATA 'CapCut\User Data\Projects\com.lveditor.draft' }
if (Test-Path $drafts) { Row 'CapCut projects folder' 'OK' $drafts } else { Row 'CapCut projects folder' 'MISSING' "open CapCut once; expected $drafts (or set CAPCUT_DRAFTS)" }

if (Has 'git') { Row 'git' 'OK' (git --version) } else { Row 'git' 'MISSING' 'downloads the Flow MCP (Claude Code on Windows also needs Git for Windows)'; Todo 'Git for Windows' 'winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements' }
$chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe", "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") | Where-Object { Test-Path $_ }
if ($chrome) { Row 'Google Chrome' 'OK' 'Flow runs in its own Chrome window' } else { Row 'Google Chrome' 'MISSING' 'needed by the Flow MCP'; Todo 'Google Chrome' 'winget install -e --id Google.Chrome --accept-source-agreements --accept-package-agreements' }

if (Has 'claude') {
  $fl = (claude mcp get flow 2>$null) -join "`n"
  if ($fl -match 'Connected') { Row 'Flow MCP' 'OK' 'registered and connected' }
  elseif ($fl) { Row 'Flow MCP' 'WARN' "registered, not connected: restart Claude Code; sign in with 'npm run login' in $FlowDir" }
  else {
    Row 'Flow MCP' 'MISSING' 'Claude makes the voice and pictures in Google Flow through it'
    if (-not $FlowRepo) { Todo 'Flow MCP: set flow_mcp_repo in skill.config.json first' 'throw "no Flow MCP source configured"' }
    else {
      if (-not (Test-Path (Join-Path $FlowDir 'package.json'))) { Todo "Flow MCP: download to $FlowDir (keep it out of OneDrive folders)" "git clone '$FlowRepo' '$FlowDir'" }
      Todo 'Flow MCP: install its parts and build it' "Set-Location '$FlowDir'; npm install; npm run build"
      Todo 'Flow MCP: add it to Claude Code for every folder' "claude mcp add --scope user flow -- node '$FlowDir\dist\index.js'"
    }
  }
  if ((Test-Path (Join-Path $HOME '.flow-mcp\gemini-key')) -or $env:GEMINI_API_KEY) { Row 'Google AI Studio key' 'OK' 'free narration voices (key not shown)' }
  else { Row 'Google AI Studio key' 'WARN' 'optional: paste it in Flow Studio > Voice yourself (never in chat)' }
} else { Row 'Claude Code CLI' 'WARN' "'claude' is not on PATH; Flow MCP check skipped" }

$free = [math]::Round((Get-PSDrive ($HOME.Substring(0,1))).Free / 1GB)
Row 'Free disk space' $(if ($free -ge 10) { 'OK' } else { 'WARN' }) "$free GB"

if (-not $NoRender -and (Has 'npx')) {
  $T = Join-Path $env:TEMP ('csf-check-' + [guid]::NewGuid().ToString('N').Substring(0, 6)); New-Item -ItemType Directory -Force "$T\compositions", "$T\assets" | Out-Null
  Copy-Item (Join-Path $Skill 'assets\gsap.min.js') "$T\assets\"
  '{"paths":{"blocks":"compositions","assets":"assets"}}' | Set-Content "$T\hyperframes.json"
  @'
<!doctype html><html><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script></head>
<body style="margin:0;width:320px;height:180px;background:#123">
<div id="t" data-composition-id="t" data-start="0" data-duration="0.5" data-width="320" data-height="180" style="position:relative;width:320px;height:180px">
<div id="b" style="position:absolute;left:20px;top:70px;width:40px;height:40px;background:#fc0"></div></div>
<script>window.__timelines = window.__timelines || {}; const tl = gsap.timeline({ paused: true }); tl.to('#b', { x: 240, duration: 0.5, ease: 'none' }, 0); window.__timelines['t'] = tl;</script>
</body></html>
'@ | Set-Content "$T\compositions\t.html"
  Push-Location $T; npx -y "hyperframes@$HF" render -c compositions/t.html -o t.mp4 --fps 10 --quiet *> "$T\log"; Pop-Location
  if (Test-Path "$T\t.mp4") { Row 'HyperFrames test render' 'OK' "hyperframes@$HF" } else { Row 'HyperFrames test render' 'WARN' "did not finish (see $T\log)" }
} else { Row 'HyperFrames test render' 'SKIP' 'skipped' }

Write-Host "`ncapcut-story-film check (Windows, untested)`n"
$rows | Format-Table -AutoSize | Out-String | Write-Host
if ($todo.Count -eq 0) { if ($fails -eq 0) { Write-Host 'Ready. Nothing to install.'; exit 0 } else { Write-Host 'The MISSING items above are yours to do (see DETAIL).'; exit 1 } }
Write-Host 'An install would do these, in order:'
$i = 1; foreach ($t in $todo) { Write-Host ("  {0}. {1}`n     {2}" -f $i, $t.D, $t.C); $i++ }
if (-not $Install) { Write-Host "`nNothing was changed. To install: powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Install"; exit 1 }
if (-not $Yes) { $ans = Read-Host "`nInstall all of the above? [y/N]"; if ($ans -notmatch '^(y|yes)$') { Write-Host 'Nothing installed.'; exit 1 } }
"capcut-story-film setup $(Get-Date)" | Add-Content $Log
foreach ($t in $todo) {
  Write-Host "`n==> $($t.D)"; "==> $($t.D)`n> $($t.C)" | Add-Content $Log
  try { Invoke-Expression $t.C *>> $Log; Write-Host '    done'; '    done' | Add-Content $Log } catch { Write-Host "    FAILED (details in $Log)"; "    FAILED $_" | Add-Content $Log }
  $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
}
Write-Host "`nLog: $Log"
Write-Host 'Close and reopen PowerShell (new tools are found after a restart of the terminal). If the Flow MCP was added, quit Claude Code, reopen it in the same folder, sign in once with "npm run login" in the Flow MCP folder, then run the check again.'
