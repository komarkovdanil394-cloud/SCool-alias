$ErrorActionPreference = "Stop"

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:FLET_CLI_NO_RICH_OUTPUT = "1"
$env:NO_COLOR = "1"
$env:JAVA_HOME = "C:\Users\User\java\17.0.13+11"
$env:ANDROID_HOME = "C:\Users\User\Android\sdk"
$env:ANDROID_SDK_ROOT = $env:ANDROID_HOME
$env:Path = "$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:ANDROID_HOME\cmdline-tools\12.0\bin;$env:Path"

flet build apk . `
    --project scool_alias `
    --product "SCool Alias" `
    --description "School Alias party game" `
    --org com.scoolalias `
    --build-version 1.0.1 `
    --build-number 2 `
    --android-adaptive-icon-background "#090C16" `
    --splash-color "#090C16" `
    --splash-dark-color "#090C16" `
    --no-rich-output `
    --yes
