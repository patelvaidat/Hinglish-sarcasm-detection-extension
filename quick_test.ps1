# Sarcasm Detection System - Quick Test Script
# Run this after starting the backend

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sarcasm Detection System - Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$API_URL = "http://localhost:8000"

# Test 1: Health Check
Write-Host "[1/6] Testing Health Check..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$API_URL/health" -Method Get
    Write-Host "  ? Status: $($health.status)" -ForegroundColor Green
    Write-Host "  ? Mode: $($health.mode)" -ForegroundColor Green
} catch {
    Write-Host "  ? Failed: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure backend is running:" -ForegroundColor Yellow
    Write-Host "  cd backend" -ForegroundColor White
    Write-Host "  .\venv\Scripts\activate" -ForegroundColor White
    Write-Host "  python main_test.py" -ForegroundColor White
    exit
}

Write-Host ""

# Test 2: Hinglish Sarcastic Example 1
Write-Host "[2/6] Testing Hinglish Sarcastic Text #1..." -ForegroundColor Yellow
$body1 = @{
    text = "Meri cooking videos pe likes or comment o n aa rahe h"
    platform = "test"
} | ConvertTo-Json

$result1 = Invoke-RestMethod -Uri "$API_URL/predict" -Method Post -Body $body1 -ContentType "application/json"
Write-Host "  Text: 'Meri cooking videos pe likes or comment o n aa rahe h'" -ForegroundColor White
Write-Host "  Is Sarcastic: $($result1.is_sarcastic)" -ForegroundColor $(if($result1.is_sarcastic){"Green"}else{"Red"})
Write-Host "  Sarcasm Score: $([math]::Round($result1.sarcasm_score * 100, 1))%" -ForegroundColor White
Write-Host "  Confidence: $([math]::Round($result1.confidence * 100, 1))%" -ForegroundColor White

Write-Host ""

# Test 3: Hinglish Sarcastic Example 2
Write-Host "[3/6] Testing Hinglish Sarcastic Text #2..." -ForegroundColor Yellow
$body2 = @{
    text = "I Love my Rajasthan"
    platform = "test"
} | ConvertTo-Json

$result2 = Invoke-RestMethod -Uri "$API_URL/predict" -Method Post -Body $body2 -ContentType "application/json"
Write-Host "  Text: 'I Love my Rajasthan'" -ForegroundColor White
Write-Host "  Is Sarcastic: $($result2.is_sarcastic)" -ForegroundColor $(if($result2.is_sarcastic){"Green"}else{"Red"})
Write-Host "  Sarcasm Score: $([math]::Round($result2.sarcasm_score * 100, 1))%" -ForegroundColor White

Write-Host ""

# Test 4: Non-Sarcastic Example
Write-Host "[4/6] Testing Non-Sarcastic Text..." -ForegroundColor Yellow
$body3 = @{
    text = "This is a wonderful day and I am very happy"
    platform = "test"
} | ConvertTo-Json

$result3 = Invoke-RestMethod -Uri "$API_URL/predict" -Method Post -Body $body3 -ContentType "application/json"
Write-Host "  Text: 'This is a wonderful day...'" -ForegroundColor White
Write-Host "  Is Sarcastic: $($result3.is_sarcastic)" -ForegroundColor $(if(!$result3.is_sarcastic){"Green"}else{"Red"})
Write-Host "  Sarcasm Score: $([math]::Round($result3.sarcasm_score * 100, 1))%" -ForegroundColor White

Write-Host ""

# Test 5: Batch Prediction
Write-Host "[5/6] Testing Batch Prediction..." -ForegroundColor Yellow
$batchBody = @(
    @{text = "Love working on weekends!"; platform = "test"},
    @{text = "Perfect, just perfect!"; platform = "test"}
) | ConvertTo-Json

$batchResult = Invoke-RestMethod -Uri "$API_URL/predict/batch" -Method Post -Body $batchBody -ContentType "application/json"
Write-Host "  Processed: $($batchResult.Count) texts" -ForegroundColor Green
foreach ($r in $batchResult) {
    Write-Host "    - Sarcastic: $($r.is_sarcastic), Score: $([math]::Round($r.sarcasm_score * 100, 1))%" -ForegroundColor White
}

Write-Host ""

# Test 6: Statistics
Write-Host "[6/6] Getting Statistics..." -ForegroundColor Yellow
$stats = Invoke-RestMethod -Uri "$API_URL/stats" -Method Get
Write-Host "  Total Predictions: $($stats.total_predictions)" -ForegroundColor White
Write-Host "  Sarcastic Count: $($stats.sarcastic_count)" -ForegroundColor White
Write-Host "  Non-Sarcastic Count: $($stats.non_sarcastic_count)" -ForegroundColor White
Write-Host "  Sarcasm Rate: $([math]::Round($stats.sarcasm_rate * 100, 1))%" -ForegroundColor White

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ? All Tests Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Check logs: type backend\logs\predictions.jsonl" -ForegroundColor White
Write-Host "  2. Open test page: test_local.html" -ForegroundColor White
Write-Host "  3. View API docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
