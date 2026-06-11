<#
.SYNOPSIS
  Gera slides de carrossel com a API de imagem do Gemini (Nano Banana).

.DESCRIPTION
  Le GEMINI_API_KEY e GEMINI_IMAGE_MODEL do .env (nada hardcoded).
  Para cada prompt de slide, chama a API e salva o PNG em saida/.
  Aceita imagens de referencia da pasta referencias/ para guiar o estilo.

.EXAMPLE
  .\scripts\gerar_carrossel_gemini.ps1 -Prompts @(
    "Slide de capa: titulo 'Prospere com IA', fundo tiffany e dourado",
    "Slide 2: lista de 3 beneficios em cima de fundo creme elegante"
  )

.NOTES
  Trocar de modelo: edite GEMINI_IMAGE_MODEL no .env. Sem mexer no script.
#>

param(
    [Parameter(Mandatory = $true)]
    [string[]] $Prompts,

    # Pasta com imagens de referencia de estilo (opcional)
    [string] $ReferenciasDir,

    # Onde salvar os slides gerados
    [string] $SaidaDir,

    # Quantas referencias enviar junto (limite pra nao pesar o request)
    [int] $MaxReferencias = 4
)

$ErrorActionPreference = "Stop"

# Resolver caminhos padrao (PSScriptRoot nao funciona no bloco param do PS 5.1)
$raiz = Split-Path $PSScriptRoot -Parent
if ([string]::IsNullOrWhiteSpace($ReferenciasDir)) { $ReferenciasDir = Join-Path $raiz "referencias" }
if ([string]::IsNullOrWhiteSpace($SaidaDir))       { $SaidaDir       = Join-Path $raiz "saida" }

# ---------- 1. Carregar .env ----------
$envPath = Join-Path $PSScriptRoot "..\.env"
if (-not (Test-Path $envPath)) { throw "Arquivo .env nao encontrado em $envPath" }

$envVars = @{}
foreach ($line in Get-Content $envPath) {
    if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
    $idx = $line.IndexOf('=')
    $key = $line.Substring(0, $idx).Trim()
    $val = $line.Substring($idx + 1).Trim()
    $envVars[$key] = $val
}

$apiKey = $envVars['GEMINI_API_KEY']
$model  = $envVars['GEMINI_IMAGE_MODEL']

if ([string]::IsNullOrWhiteSpace($apiKey)) { throw "GEMINI_API_KEY ausente no .env" }
if ([string]::IsNullOrWhiteSpace($model))  { throw "GEMINI_IMAGE_MODEL ausente no .env" }

Write-Host "Modelo em uso: $model" -ForegroundColor Cyan

# ---------- 2. Coletar referencias ----------
$refParts = @()
if (Test-Path $ReferenciasDir) {
    $refFiles = Get-ChildItem $ReferenciasDir -File |
        Where-Object { $_.Extension -match '\.(jpg|jpeg|png|webp)$' } |
        Select-Object -First $MaxReferencias
    foreach ($f in $refFiles) {
        $bytes  = [IO.File]::ReadAllBytes($f.FullName)
        $b64    = [Convert]::ToBase64String($bytes)
        $mime   = switch ($f.Extension.ToLower()) {
            '.png'  { 'image/png' }
            '.webp' { 'image/webp' }
            default { 'image/jpeg' }
        }
        $refParts += @{ inline_data = @{ mime_type = $mime; data = $b64 } }
        Write-Host "  referencia: $($f.Name)" -ForegroundColor DarkGray
    }
}

# ---------- 3. Gerar cada slide ----------
if (-not (Test-Path $SaidaDir)) { New-Item -ItemType Directory -Path $SaidaDir | Out-Null }

$endpoint = "https://generativelanguage.googleapis.com/v1beta/models/$($model):generateContent"
$headers  = @{ 'x-goog-api-key' = $apiKey; 'Content-Type' = 'application/json' }

$slideNum = 0
foreach ($prompt in $Prompts) {
    $slideNum++
    Write-Host "`nGerando slide $slideNum/$($Prompts.Count)..." -ForegroundColor Yellow

    $estilo = "Formato Instagram carrossel 1080x1350 (4:5), vertical. " +
              "Paleta da marca: tiffany, petroleo, creme e dourado. " +
              "Visual elegante, sofisticado, alta qualidade. "

    $parts = @( @{ text = "$estilo`n$prompt" } )
    $parts += $refParts   # referencias depois do texto

    $body = @{
        contents = @(@{ parts = $parts })
        generationConfig = @{ responseModalities = @('IMAGE') }
    } | ConvertTo-Json -Depth 12

    try {
        $resp = Invoke-RestMethod -Uri $endpoint -Method Post -Headers $headers -Body $body
    } catch {
        Write-Host "  ERRO na API: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message -ForegroundColor Red }
        continue
    }

    $imgPart = $resp.candidates[0].content.parts |
        Where-Object { $_.inline_data -or $_.inlineData } | Select-Object -First 1
    $data = if ($imgPart.inline_data) { $imgPart.inline_data.data } else { $imgPart.inlineData.data }

    if ([string]::IsNullOrWhiteSpace($data)) {
        Write-Host "  Sem imagem retornada para o slide $slideNum." -ForegroundColor Red
        continue
    }

    $outFile = Join-Path $SaidaDir ("slide_{0:D2}.png" -f $slideNum)
    [IO.File]::WriteAllBytes($outFile, [Convert]::FromBase64String($data))
    Write-Host "  salvo: $outFile" -ForegroundColor Green
}

Write-Host "`nPronto. Slides em: $SaidaDir" -ForegroundColor Cyan
