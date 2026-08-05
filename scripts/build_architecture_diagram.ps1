param(
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

$repoPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $OutputPath) {
    $OutputPath = Join-Path $repoPath "assets\proofline-architecture.png"
}

$width = 1536
$height = 1024
$bitmap = [Drawing.Bitmap]::new($width, $height)
$graphics = [Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.TextRenderingHint = [Drawing.Text.TextRenderingHint]::ClearTypeGridFit

$background = [Drawing.Color]::FromArgb(8, 17, 35)
$panel = [Drawing.Color]::FromArgb(17, 32, 57)
$live = [Drawing.Color]::FromArgb(26, 184, 229)
$gate = [Drawing.Color]::FromArgb(247, 194, 66)
$planned = [Drawing.Color]::FromArgb(125, 139, 164)
$white = [Drawing.Color]::FromArgb(241, 247, 255)
$muted = [Drawing.Color]::FromArgb(164, 180, 204)
$green = [Drawing.Color]::FromArgb(67, 211, 142)

$graphics.Clear($background)
$titleFont = [Drawing.Font]::new("Segoe UI", 34, [Drawing.FontStyle]::Bold)
$subtitleFont = [Drawing.Font]::new("Segoe UI", 17, [Drawing.FontStyle]::Regular)
$boxFont = [Drawing.Font]::new("Segoe UI", 17, [Drawing.FontStyle]::Bold)
$smallFont = [Drawing.Font]::new("Segoe UI", 13, [Drawing.FontStyle]::Regular)
$tinyFont = [Drawing.Font]::new("Segoe UI", 11, [Drawing.FontStyle]::Regular)

function Draw-CenteredText {
    param([string]$Text, [Drawing.RectangleF]$Rect, [Drawing.Font]$Font, [Drawing.Color]$Color)
    $format = [Drawing.StringFormat]::new()
    $format.Alignment = [Drawing.StringAlignment]::Center
    $format.LineAlignment = [Drawing.StringAlignment]::Center
    $graphics.DrawString($Text, $Font, [Drawing.SolidBrush]::new($Color), $Rect, $format)
    $format.Dispose()
}

function Draw-Box {
    param([Drawing.RectangleF]$Rect, [string]$Text, [Drawing.Color]$Border, [bool]$Dashed = $false)
    $path = [Drawing.Drawing2D.GraphicsPath]::new()
    $radius = 22.0
    $diameter = $radius * 2
    $path.AddArc($Rect.X, $Rect.Y, $diameter, $diameter, 180, 90)
    $path.AddArc($Rect.Right - $diameter, $Rect.Y, $diameter, $diameter, 270, 90)
    $path.AddArc($Rect.Right - $diameter, $Rect.Bottom - $diameter, $diameter, $diameter, 0, 90)
    $path.AddArc($Rect.X, $Rect.Bottom - $diameter, $diameter, $diameter, 90, 90)
    $path.CloseFigure()
    $graphics.FillPath([Drawing.SolidBrush]::new($panel), $path)
    $pen = [Drawing.Pen]::new($Border, 4)
    if ($Dashed) { $pen.DashStyle = [Drawing.Drawing2D.DashStyle]::Dash }
    $graphics.DrawPath($pen, $path)
    Draw-CenteredText $Text $Rect $boxFont $white
    $pen.Dispose()
    $path.Dispose()
}

function Draw-Arrow {
    param([Drawing.PointF]$From, [Drawing.PointF]$To, [Drawing.Color]$Color, [bool]$Dashed = $false)
    $pen = [Drawing.Pen]::new($Color, 4)
    $pen.CustomEndCap = [Drawing.Drawing2D.AdjustableArrowCap]::new(6, 8)
    if ($Dashed) { $pen.DashStyle = [Drawing.Drawing2D.DashStyle]::Dash }
    $graphics.DrawLine($pen, $From, $To)
    $pen.Dispose()
}

$graphics.DrawString("PROOFLINE ARCHITECTURE", $titleFont, [Drawing.SolidBrush]::new($white), 72, 56)
$graphics.DrawString("Verification-first agent | live path and planned extensions shown separately", $subtitleFont, [Drawing.SolidBrush]::new($muted), 75, 115)

$cloud = [Drawing.RectangleF]::new(80, 245, 225, 115)
$agent = [Drawing.RectangleF]::new(380, 225, 285, 155)
$proofGate = [Drawing.RectangleF]::new(745, 225, 260, 155)
$packet = [Drawing.RectangleF]::new(1085, 245, 250, 115)
$sources = [Drawing.RectangleF]::new(745, 485, 260, 115)
$approval = [Drawing.RectangleF]::new(1085, 485, 250, 115)
$action = [Drawing.RectangleF]::new(1085, 705, 250, 115)
$firestore = [Drawing.RectangleF]::new(380, 705, 285, 115)
$pubsub = [Drawing.RectangleF]::new(745, 705, 260, 115)

Draw-Box $cloud "Cloud Run API`nDEPLOYED" $green
Draw-Box $agent "Gemini 3.6 Flash`n+ Google ADK" $live
Draw-Box $proofGate "Deterministic`nProofline gate" $gate
Draw-Box $packet "Hash-addressed`nproof packet" $live
Draw-Box $sources "Fresh authoritative`nevidence" $live
Draw-Box $approval "Human approval`nboundary" $gate
Draw-Box $action "External action`n(only after approval)" $green
Draw-Box $firestore "Firestore`ndurable packets" $planned $true
Draw-Box $pubsub "Pub/Sub`nasync rechecks" $planned $true

Draw-Arrow ([Drawing.PointF]::new($cloud.Right, 302)) ([Drawing.PointF]::new($agent.Left, 302)) $green
Draw-Arrow ([Drawing.PointF]::new($agent.Right, 302)) ([Drawing.PointF]::new($proofGate.Left, 302)) $live
Draw-Arrow ([Drawing.PointF]::new($sources.X + 130, $sources.Top)) ([Drawing.PointF]::new($proofGate.X + 130, $proofGate.Bottom)) $live
Draw-Arrow ([Drawing.PointF]::new($proofGate.Right, 302)) ([Drawing.PointF]::new($packet.Left, 302)) $gate
Draw-Arrow ([Drawing.PointF]::new($packet.X + 125, $packet.Bottom)) ([Drawing.PointF]::new($approval.X + 125, $approval.Top)) $gate
Draw-Arrow ([Drawing.PointF]::new($approval.X + 125, $approval.Bottom)) ([Drawing.PointF]::new($action.X + 125, $action.Top)) $green
Draw-Arrow ([Drawing.PointF]::new($firestore.Right, 762)) ([Drawing.PointF]::new($pubsub.Left, 762)) $planned $true
Draw-Arrow ([Drawing.PointF]::new($pubsub.X + 130, $pubsub.Top)) ([Drawing.PointF]::new($sources.X + 130, $sources.Bottom)) $planned $true

$graphics.DrawString("LIVE, VERIFIED FLOW", $smallFont, [Drawing.SolidBrush]::new($green), 82, 195)
$graphics.DrawString("PLANNED EXTENSIONS", $smallFont, [Drawing.SolidBrush]::new($planned), 380, 660)
$graphics.DrawString("Model output cannot override the deterministic gate. Missing, stale, or conflicting evidence never returns READY.", $smallFont, [Drawing.SolidBrush]::new($muted), 80, 885)
$graphics.DrawString("AI-assisted diagram | Architecture reflects public repository commit and verified Cloud Run deployment", $tinyFont, [Drawing.SolidBrush]::new($muted), 80, 935)

$directory = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Path $directory -Force | Out-Null
$bitmap.Save($OutputPath, [Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

[pscustomobject]@{
    output = (Resolve-Path $OutputPath).Path
    width = $width
    height = $height
} | ConvertTo-Json
