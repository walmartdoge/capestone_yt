function Find-CodeCmd {
    if (Get-Command code -ErrorAction SilentlyContinue) { return "code" }
    $commonPaths = @(
        "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd",
        "$env:ProgramFiles\Microsoft VS Code\bin\code.cmd",
        "${env:ProgramFiles(x86)}\Microsoft VS Code\bin\code.cmd"
    )
    foreach ($path in $commonPaths) {
        if (Test-Path $path) { return $path }
    }
    return $null
}

$codeCmd = Find-CodeCmd
if ($null -eq $codeCmd) { return }

$extensions = @(
    "innoverio.vscode-dbt-power-user",
    "ms-python.python",
    "samuelcolvin.jinjahtml",
    "redhat.vscode-yaml",
    "cldwalker.clickhouse-language-support"
)

foreach ($ext in $extensions) {
    & $codeCmd --install-extension $ext --force | Out-Null
}
