# 作业2 · 演示脚本：复现录屏里的全过程
# 用法：pwsh -File tools/record_demo.ps1
# 作用：① 展示已注册的定时任务 ② 手动触发（与定时触发同一条路径）③ 实时看日志 ④ 拉取邮箱里的日报自证

param(
    [string]$Title = 'AI日报机器-演示',
    [string]$Flag = 'demo_done.flag'
)
$ErrorActionPreference = 'Continue'
$dir = Split-Path -Parent $PSScriptRoot
Set-Location $dir
$log = Join-Path $dir 'logs\task_console.log'
$Host.UI.RawUI.WindowTitle = $Title

function Say($t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }

Clear-Host
Say "作业2 · 定期开工的机器 —— 定时任务演示"
Write-Host "本机时区时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

Say "[1] 已注册的定时任务（每天 08:00 自动拉起，无需人管）"
schtasks /query /tn "AI日报机器" /fo LIST /v |
    Select-String -Pattern 'Next Run Time|Last Run Time|Last Result|Task To Run' |
    ForEach-Object { "   " + $_.Line.Trim() }
Start-Sleep -Seconds 3

Say "[2] 手动触发一次（与到点自动触发完全同一条路径）"
$before = 0
if (Test-Path $log) { $before = (Get-Content $log).Count }
schtasks /run /tn "AI日报机器" | ForEach-Object { "   " + $_ }
Start-Sleep -Seconds 3

Say "[3] 任务已被任务计划程序拉起，控制台日志实时输出"
$deadline = (Get-Date).AddMinutes(6)
$seen = 0
$done = $false
while ((Get-Date) -lt $deadline -and -not $done) {
    if (Test-Path $log) {
        $lines = @(Get-Content $log)
        if ($lines.Count -gt $seen) {
            $lines[$seen..($lines.Count - 1)] | ForEach-Object { Write-Host $_ }
            $seen = $lines.Count
        }
        # 只认「本次触发之后」新出现的 task finished 行
        if ($lines.Count -gt $before -and ($lines[$before..($lines.Count - 1)] -match 'task finished')) { $done = $true }
    }
    Start-Sleep -Seconds 2
}

Say "[4] 任务运行结果"
schtasks /query /tn "AI日报机器" /fo LIST /v |
    Select-String -Pattern 'Last Run Time|Last Result' |
    ForEach-Object { "   " + $_.Line.Trim() }
Start-Sleep -Seconds 2

Say "[5] 用 IMAP 回读自己邮箱里的最新一封日报（收信自证）"
& "$dir\.venv\Scripts\python.exe" "$dir\tools\imap_check.py" | ForEach-Object { "   " + $_ }
Start-Sleep -Seconds 2
if (Test-Path (Join-Path $dir 'logs\latest_mail.txt')) {
    Get-Content (Join-Path $dir 'logs\latest_mail.txt') -TotalCount 28 | ForEach-Object { Write-Host $_ }
}

Say "演示结束"
Set-Content -Path (Join-Path $dir "logs\$Flag") -Value (Get-Date -Format 's')
Start-Sleep -Seconds 5
