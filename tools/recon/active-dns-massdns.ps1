param(
    [Parameter(Mandatory = $true)]
    [string]$Domain,

    [Parameter(Mandatory = $true)]
    [string]$Dictionary,

    [Parameter(Mandatory = $true)]
    [string]$ResolversFile,

    [Parameter(Mandatory = $true)]
    [string]$OutputDir,

    [Parameter(Mandatory = $true)]
    [string]$RawDir,

    [string[]]$Canary = @(),

    [string]$Nonce = "",

    [string]$Massdns = "tools/third-party/bin/massdns.exe",

    [int]$HashmapSize = 10000,

    [string]$RecordType = "A"
)

$ErrorActionPreference = "Stop"

function Resolve-LocalPath {
    param([string]$PathText)
    if ([System.IO.Path]::IsPathRooted($PathText)) {
        return [System.IO.Path]::GetFullPath($PathText)
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location) $PathText))
}

function Normalize-Domain {
    param([string]$Value)
    $normalized = $Value.Trim().ToLowerInvariant().TrimEnd(".")
    if ($normalized.StartsWith("*.")) {
        $normalized = $normalized.Substring(2)
    }
    return $normalized
}

function Join-Target {
    param(
        [string]$Value,
        [string]$RootDomain
    )
    $target = $Value.Trim().ToLowerInvariant().TrimEnd(".")
    if ($target.Length -eq 0) {
        return ""
    }
    if ($target -eq $RootDomain -or $target.EndsWith(".$RootDomain")) {
        return $target
    }
    return "$target.$RootDomain"
}

function Write-LinesAscii {
    param(
        [string]$PathText,
        [string[]]$Lines
    )
    $Lines | Set-Content -Path $PathText -Encoding ascii
}

function Invoke-TimedStep {
    param(
        [string]$Name,
        [scriptblock]$Block
    )
    $started = Get-Date
    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    $exitCode = 0
    try {
        & $Block
        if ($null -ne $global:LASTEXITCODE) {
            $exitCode = [int]$global:LASTEXITCODE
        }
    }
    catch {
        $exitCode = 1
        throw
    }
    finally {
        $watch.Stop()
        $script:Metrics += [pscustomobject]@{
            step = $Name
            start = $started.ToString("s")
            elapsed_seconds = [math]::Round($watch.Elapsed.TotalSeconds, 3)
            exit = $exitCode
        }
    }
    if ($exitCode -ne 0) {
        throw "Step failed: $Name exit=$exitCode"
    }
}

function Invoke-MassdnsFile {
    param(
        [string]$InputFile,
        [string]$ResolverFile,
        [string]$OutputFile
    )
    & $MassdnsPath -q -r $ResolverFile -o Snl -t $RecordType --root --retry REFUSED --retry SERVFAIL -w $OutputFile -s $HashmapSize $InputFile
}

function Get-MassdnsHosts {
    param([string]$MassdnsOutput)
    $hosts = New-Object "System.Collections.Generic.HashSet[string]"
    if (-not (Test-Path $MassdnsOutput)) {
        return $hosts
    }
    foreach ($line in Get-Content -Path $MassdnsOutput) {
        if ($line -match "^\s*([^\s]+)\s+(A|AAAA|CNAME)\s+") {
            $hostName = $matches[1].TrimEnd(".").ToLowerInvariant()
            [void]$hosts.Add($hostName)
        }
    }
    return $hosts
}

function Write-HostSet {
    param(
        [System.Collections.Generic.HashSet[string]]$Hosts,
        [string]$PathText
    )
    $Hosts | Sort-Object | Set-Content -Path $PathText -Encoding ascii
}

$RootDomain = Normalize-Domain $Domain
$DictionaryPath = Resolve-LocalPath $Dictionary
$ResolversPath = Resolve-LocalPath $ResolversFile
$OutputPath = Resolve-LocalPath $OutputDir
$RawPath = Resolve-LocalPath $RawDir
$MassdnsPath = Resolve-LocalPath $Massdns

if (-not (Test-Path $DictionaryPath)) {
    throw "Dictionary does not exist: $DictionaryPath"
}
if (-not (Test-Path $ResolversPath)) {
    throw "Resolvers file does not exist: $ResolversPath"
}
if (-not (Test-Path $MassdnsPath)) {
    throw "massdns does not exist: $MassdnsPath"
}

New-Item -ItemType Directory -Force $OutputPath, $RawPath | Out-Null

$script:Metrics = @()
$summary = [ordered]@{
    status = "running"
    engine = "massdns-direct"
    domain = $RootDomain
    dictionary = $DictionaryPath
    resolvers_file = $ResolversPath
    record_type = $RecordType
    hashmap_size = $HashmapSize
    candidate_count = 0
    hits = 0
    wildcard_suspected = $false
}

$candidatesFile = Join-Path $RawPath "active-dns-candidates.txt"
$hitsFile = Join-Path $RawPath "active-dns-hits.txt"
$massdnsFile = Join-Path $RawPath "active-dns-massdns.txt"
$canaryFile = Join-Path $OutputPath "active-dns-canary-targets.txt"
$nxFile = Join-Path $OutputPath "active-dns-nxdomain-targets.txt"
$effectiveResolversFile = Join-Path $OutputPath "active-dns-effective-resolvers.txt"
$metricsFile = Join-Path $OutputPath "active-dns-metrics.json"
$summaryJsonFile = Join-Path $OutputPath "active-dns-summary.json"
$summaryMdFile = Join-Path $OutputPath "active-dns-summary.md"
$script:Failed = $false
$script:FailureMessage = ""

try {
    $resolverList = @(Get-Content -Path $ResolversPath | ForEach-Object { $_.Trim() } | Where-Object { $_ })
    if ($resolverList.Count -eq 0) {
        throw "Resolvers file is empty: $ResolversPath"
    }
    $summary.resolvers = $resolverList

    $canaryTargets = @($Canary | ForEach-Object { Join-Target $_ $RootDomain } | Where-Object { $_ })
    Write-LinesAscii $canaryFile $canaryTargets
    $summary.canary_targets = $canaryTargets

    if ($Nonce.Trim().Length -eq 0) {
        $Nonce = "nx-" + (Get-Date -Format "yyyyMMddHHmmss")
    }
    $nxTarget = Join-Target $Nonce $RootDomain
    Write-LinesAscii $nxFile @($nxTarget)
    $summary.nxdomain_target = $nxTarget

    $healthyResolvers = New-Object "System.Collections.Generic.List[string]"
    if ($canaryTargets.Count -gt 0) {
        Invoke-TimedStep "canary_massdns" {
            Invoke-MassdnsFile $canaryFile $ResolversPath (Join-Path $RawPath "active-dns-canary-massdns.txt")
        }
        $canaryHosts = Get-MassdnsHosts (Join-Path $RawPath "active-dns-canary-massdns.txt")
        $summary.canary_hits = $canaryHosts.Count
        if ($canaryHosts.Count -eq 0) {
            throw "Canary has no DNS hit; stop before full enumeration."
        }

        foreach ($resolver in $resolverList) {
            $safeResolver = ($resolver -replace "[^a-zA-Z0-9]+", "-").Trim("-")
            $singleResolverFile = Join-Path $OutputPath "resolver-$safeResolver.txt"
            $resolverOutputFile = Join-Path $RawPath "resolver-health-$safeResolver-massdns.txt"
            Write-LinesAscii $singleResolverFile @($resolver)
            Invoke-TimedStep "resolver_$safeResolver" {
                Invoke-MassdnsFile $canaryFile $singleResolverFile $resolverOutputFile
            }
            $resolverHosts = Get-MassdnsHosts $resolverOutputFile
            if ($resolverHosts.Count -gt 0) {
                [void]$healthyResolvers.Add($resolver)
            }
        }
    }
    else {
        foreach ($resolver in $resolverList) {
            [void]$healthyResolvers.Add($resolver)
        }
    }

    if ($healthyResolvers.Count -eq 0) {
        throw "No healthy resolver remains."
    }
    Write-LinesAscii $effectiveResolversFile $healthyResolvers.ToArray()
    $summary.effective_resolvers = $healthyResolvers.ToArray()

    Invoke-TimedStep "nxdomain_massdns" {
        Invoke-MassdnsFile $nxFile $effectiveResolversFile (Join-Path $RawPath "active-dns-nxdomain-massdns.txt")
    }
    $nxHosts = Get-MassdnsHosts (Join-Path $RawPath "active-dns-nxdomain-massdns.txt")
    $summary.nxdomain_hits = $nxHosts.Count
    $summary.wildcard_suspected = ($nxHosts.Count -gt 0)
    if ($nxHosts.Count -gt 0) {
        throw "NXDOMAIN returned DNS records; wildcard suspected, stop before full enumeration."
    }

    Invoke-TimedStep "generate_candidates" {
        $candidateCount = 0
        $reader = [System.IO.StreamReader]::new($DictionaryPath)
        $writer = [System.IO.StreamWriter]::new($candidatesFile, $false, [System.Text.Encoding]::ASCII)
        try {
            while (($line = $reader.ReadLine()) -ne $null) {
                $word = $line.Trim().TrimEnd(".").ToLowerInvariant()
                if ($word.Length -eq 0 -or $word.StartsWith("#")) {
                    continue
                }
                if ($word -eq $RootDomain -or $word.EndsWith(".$RootDomain")) {
                    $writer.WriteLine($word)
                }
                else {
                    $writer.WriteLine("$word.$RootDomain")
                }
                $candidateCount += 1
            }
        }
        finally {
            $writer.Dispose()
            $reader.Dispose()
        }
        $script:CandidateCount = $candidateCount
    }
    $summary.candidate_count = $script:CandidateCount

    Invoke-TimedStep "massdns_full_enum" {
        Invoke-MassdnsFile $candidatesFile $effectiveResolversFile $massdnsFile
    }
    Invoke-TimedStep "extract_hits" {
        $script:HitHosts = Get-MassdnsHosts $massdnsFile
        Write-HostSet $script:HitHosts $hitsFile
    }
    $summary.hits = $script:HitHosts.Count
    $summary.files = [ordered]@{
        candidates = $candidatesFile
        massdns = $massdnsFile
        hits = $hitsFile
        metrics = $metricsFile
        summary_json = $summaryJsonFile
        summary_md = $summaryMdFile
    }
    $summary.status = "success"
}
catch {
    $script:Failed = $true
    $script:FailureMessage = $_.Exception.Message
    $summary.status = "failed"
    $summary.error = $script:FailureMessage
}
finally {
    $script:Metrics | ConvertTo-Json -Depth 5 | Set-Content -Path $metricsFile -Encoding utf8

    $totalElapsed = [math]::Round((($script:Metrics | Measure-Object -Property elapsed_seconds -Sum).Sum), 3)
    $summary.total_elapsed_seconds = $totalElapsed
    $summary.generated_at = (Get-Date).ToString("s")
    $summary | ConvertTo-Json -Depth 8 | Set-Content -Path $summaryJsonFile -Encoding utf8

    $md = @(
        "# Active DNS massdns direct summary",
        "",
        "- Status: $($summary.status)",
        "- Engine: massdns-direct",
        "- Domain: $RootDomain",
        "- Candidates: $($summary.candidate_count)",
        "- Hits: $($summary.hits)",
        "- Total elapsed: ${totalElapsed}s",
        "- Wildcard suspected: $($summary.wildcard_suspected)"
    )
    if ($script:Failed) {
        $md += "- Error: $script:FailureMessage"
    }
    $md += @(
        "",
        "## Files",
        "",
        "- Candidates: $candidatesFile",
        "- Raw massdns: $massdnsFile",
        "- Hits: $hitsFile",
        "- Metrics: $metricsFile",
        "",
        "## Metrics",
        "",
        "| Step | Elapsed | Exit |",
        "| --- | ---: | ---: |"
    )
    foreach ($metric in $script:Metrics) {
        $md += "| $($metric.step) | $($metric.elapsed_seconds)s | $($metric.exit) |"
    }
    $md | Set-Content -Path $summaryMdFile -Encoding utf8
}

if ($script:Failed) {
    Write-Error $script:FailureMessage
    exit 1
}

Write-Host "massdns-direct complete: domain=$RootDomain candidates=$($summary.candidate_count) hits=$($summary.hits) elapsed=${totalElapsed}s"
Write-Host "hits: $hitsFile"
Write-Host "metrics: $metricsFile"
