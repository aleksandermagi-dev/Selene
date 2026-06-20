param(
    [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"

$root = if ($OutDir) {
    $OutDir
} else {
    Join-Path $env:USERPROFILE "Tools\SeleneBruno"
}

$collectionDir = Join-Path $root "Selene Local Sidecar"
$requestsDir = Join-Path $collectionDir "requests"
New-Item -ItemType Directory -Force -Path $requestsDir | Out-Null

@"
{
  "version": "1",
  "name": "Selene Local Sidecar",
  "type": "collection",
  "ignore": [
    "node_modules",
    ".git"
  ]
}
"@ | Set-Content -LiteralPath (Join-Path $collectionDir "bruno.json") -Encoding UTF8

@"
vars {
  baseUrl: http://127.0.0.1:8766
}
"@ | Set-Content -LiteralPath (Join-Path $collectionDir "environments.bru") -Encoding UTF8

$requests = @(
    @{ name = "Health"; file = "health.bru"; method = "get"; path = "/health" },
    @{ name = "C Vessel Status"; file = "c-vessel-status.bru"; method = "get"; path = "/api/c-vessel/status" },
    @{ name = "Transfer Gate Preview"; file = "transfer-gate-preview.bru"; method = "get"; path = "/api/c-vessel/transfer-gate/preview" },
    @{ name = "Vessel Construction Status"; file = "vessel-construction-status.bru"; method = "get"; path = "/api/vessel/construction/status" },
    @{ name = "Steps 1-8 Status"; file = "steps-1-8-status.bru"; method = "get"; path = "/api/vessel/steps-1-8/status" },
    @{ name = "Review Queue"; file = "review-queue.bru"; method = "get"; path = "/api/vessel/review-queue?limit=10" },
    @{ name = "Gap Scaffold Readiness"; file = "gap-scaffold-readiness.bru"; method = "get"; path = "/api/vessel/gap-scaffold/readiness" },
    @{ name = "Semantic Status"; file = "semantic-status.bru"; method = "get"; path = "/api/semantic/status" },
    @{ name = "Prepare Vessel Pieces"; file = "prepare-vessel-pieces.bru"; method = "post"; path = "/api/vessel/construction/prepare"; body = '{"scope":"buildable_vessel_pieces_only_no_transfer"}' },
    @{ name = "Ensure Organ Contracts"; file = "ensure-organ-contracts.bru"; method = "post"; path = "/api/vessel/organ-contracts/ensure"; body = '{}' },
    @{ name = "Ensure Gap Targets"; file = "ensure-gap-targets.bru"; method = "post"; path = "/api/vessel/gap-targets/ensure"; body = '{}' },
    @{ name = "Create All Gap Scaffolds"; file = "create-all-gap-scaffolds.bru"; method = "post"; path = "/api/vessel/gap-scaffold/create-all"; body = '{}' },
    @{ name = "Reasoning Check Diagnostic"; file = "reasoning-check-diagnostic.bru"; method = "post"; path = "/api/vessel/reasoning-check"; body = '{"prompt":"Run a bounded reasoning diagnostic for review-only Selene readiness.","expected":"Report diagnostic status only."}' },
    @{ name = "Fluency Diagnostic"; file = "fluency-diagnostic.bru"; method = "post"; path = "/api/vessel/fluency-diagnostic"; body = '{"sample":"Selene local readiness diagnostic sample.","purpose":"diagnostic_only"}' },
    @{ name = "Reconstruction Readiness"; file = "reconstruction-readiness.bru"; method = "post"; path = "/api/vessel/reconstruction-readiness"; body = '{"scope":"review_only_readiness"}' },
    @{ name = "Public Release Sync No Push"; file = "public-release-sync-no-push.bru"; method = "post"; path = "/api/public-release/sync"; body = '{"push":false}' }
)

foreach ($request in $requests) {
    $bodyMode = if ($request.method -eq "post") { "json" } else { "none" }
    $bodyBlock = if ($request.method -eq "post") {
        @"

body:json {
$($request.body)
}
"@
    } else {
        ""
    }
    @"
meta {
  name: $($request.name)
  type: http
  seq: 1
}

$($request.method) {
  url: {{baseUrl}}$($request.path)
  body: $bodyMode
  auth: none
}
$bodyBlock
"@ | Set-Content -LiteralPath (Join-Path $requestsDir $request.file) -Encoding UTF8
}

[ordered]@{
    status = "bruno_collection_seeded"
    collection_path = (Resolve-Path -LiteralPath $collectionDir).Path
    tracked_in_repo = $false
    request_count = $requests.Count
    safety_note = "This collection is outside the Selene repo by default. Do not add it to git unless explicitly approved."
    created_at = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json -Depth 4
