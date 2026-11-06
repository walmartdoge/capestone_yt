if (Get-Command python -ErrorAction SilentlyContinue) {
    python "$PSScriptRoot/setup.py"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 "$PSScriptRoot/setup.py"
} else {
    Write-Host "CHYBA: Python nebyl nalezen." -ForegroundColor Red
}
