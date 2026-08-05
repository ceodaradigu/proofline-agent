param(
    [string]$Voice = "Microsoft Zira Desktop",
    [int]$Rate = 0
)

$ErrorActionPreference = "Stop"
$repoPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$scriptPath = Join-Path $repoPath "video\script.json"
$imagePath = Join-Path $repoPath "devpost-thumbnail.png"
$buildPath = Join-Path $repoPath "video\build"
$outputPath = Join-Path $repoPath "video\proofline-demo-draft.mp4"

$ffmpeg = (Get-Command ffmpeg -ErrorAction Stop).Source
$ffprobe = (Get-Command ffprobe -ErrorAction Stop).Source
Add-Type -AssemblyName System.Speech

New-Item -ItemType Directory -Path $buildPath -Force | Out-Null
$segments = Get-Content -LiteralPath $scriptPath -Raw | ConvertFrom-Json
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice($Voice)
$synth.Rate = $Rate

$audioFiles = @()
$durations = @()
for ($index = 0; $index -lt $segments.Count; $index++) {
    $audioPath = Join-Path $buildPath ("segment-{0:D2}.wav" -f ($index + 1))
    $synth.SetOutputToWaveFile($audioPath)
    $synth.Speak($segments[$index].narration)
    $synth.SetOutputToNull()
    $duration = [double](& $ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $audioPath)
    $audioFiles += $audioPath
    $durations += $duration
}
$synth.Dispose()

$concatPath = Join-Path $buildPath "audio-concat.txt"
$concatLines = $audioFiles | ForEach-Object { "file '$($_.Replace("'", "''"))'" }
[IO.File]::WriteAllLines($concatPath, $concatLines, [Text.UTF8Encoding]::new($false))
$narrationPath = Join-Path $buildPath "narration.wav"
& $ffmpeg -y -v error -f concat -safe 0 -i $concatPath -c copy $narrationPath
if ($LASTEXITCODE -ne 0) { throw "FFmpeg could not concatenate narration." }

function Format-AssTime([double]$seconds) {
    $span = [TimeSpan]::FromSeconds($seconds)
    return "{0}:{1:D2}:{2:D2}.{3:D2}" -f [int]$span.TotalHours, $span.Minutes, $span.Seconds, [int]($span.Milliseconds / 10)
}

function Escape-AssText([string]$text) {
    return $text.Replace("\", "\\").Replace("{", "\{").Replace("}", "\}").Replace("`r", " ").Replace("`n", " ")
}

$assPath = Join-Path $buildPath "captions.ass"
$assLines = [Collections.Generic.List[string]]::new()
$assLines.Add("[Script Info]")
$assLines.Add("ScriptType: v4.00+")
$assLines.Add("PlayResX: 1920")
$assLines.Add("PlayResY: 1080")
$assLines.Add("")
$assLines.Add("[V4+ Styles]")
$assLines.Add("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding")
$assLines.Add("Style: Caption,Arial,40,&H00FFFFFF,&H000000FF,&H00101A2D,&HA0101A2D,0,0,0,0,100,100,0,0,3,1,0,2,130,130,55,1")
$assLines.Add("Style: Section,Arial,44,&H00F7D37A,&H000000FF,&H00101A2D,&HA0101A2D,-1,0,0,0,100,100,0,0,3,1,0,8,160,160,55,1")
$assLines.Add("Style: Disclosure,Arial,26,&H00FFFFFF,&H000000FF,&H00101A2D,&HA0101A2D,0,0,0,0,100,100,0,0,3,1,0,7,35,35,28,1")
$assLines.Add("")
$assLines.Add("[Events]")
$assLines.Add("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text")

$totalDuration = ($durations | Measure-Object -Sum).Sum
$assLines.Add("Dialogue: 0,0:00:00.00,$(Format-AssTime $totalDuration),Disclosure,,0,0,0,,AI-assisted production | Synthetic fixtures | Cloud deployment not yet claimed")

$cursor = 0.0
for ($index = 0; $index -lt $segments.Count; $index++) {
    $segment = $segments[$index]
    $segmentStart = $cursor
    $segmentEnd = $cursor + $durations[$index]
    $assLines.Add("Dialogue: 1,$(Format-AssTime $segmentStart),$(Format-AssTime $segmentEnd),Section,,0,0,0,,$(Escape-AssText $segment.title)")

    $sentences = [regex]::Split($segment.narration.Trim(), "(?<=[.!?])\s+") | Where-Object { $_.Trim() }
    $weights = $sentences | ForEach-Object { [Math]::Max($_.Length, 1) }
    $weightTotal = ($weights | Measure-Object -Sum).Sum
    $captionCursor = $segmentStart
    for ($sentenceIndex = 0; $sentenceIndex -lt $sentences.Count; $sentenceIndex++) {
        $share = $durations[$index] * ($weights[$sentenceIndex] / $weightTotal)
        $captionEnd = if ($sentenceIndex -eq $sentences.Count - 1) { $segmentEnd } else { $captionCursor + $share }
        $assLines.Add("Dialogue: 2,$(Format-AssTime $captionCursor),$(Format-AssTime $captionEnd),Caption,,0,0,0,,$(Escape-AssText $sentences[$sentenceIndex])")
        $captionCursor = $captionEnd
    }
    $cursor = $segmentEnd
}

[IO.File]::WriteAllLines($assPath, $assLines, [Text.UTF8Encoding]::new($false))
$filter = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,subtitles=video/build/captions.ass"
& $ffmpeg -y -v error -loop 1 -framerate 24 -i $imagePath -i $narrationPath -vf $filter -c:v libx264 -preset veryfast -tune stillimage -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart $outputPath
if ($LASTEXITCODE -ne 0) { throw "FFmpeg could not render the demo video." }

$videoDuration = [double](& $ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $outputPath)
$videoSize = (Get-Item -LiteralPath $outputPath).Length
[pscustomobject]@{
    output = $outputPath
    duration_seconds = [Math]::Round($videoDuration, 2)
    size_bytes = $videoSize
    segments = $segments.Count
    voice = $Voice
    rate = $Rate
} | ConvertTo-Json
