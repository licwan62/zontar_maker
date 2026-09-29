$package = ".\Toyota_Land_Cruiser_Tozaroa_最终上架包"
$files = @()
$files += Get-ChildItem -LiteralPath "$package\01_主图" -Filter *.png
$files += Get-ChildItem -LiteralPath "$package\02_车型适配图" -Filter *.png
$files += Get-ChildItem -LiteralPath "$package\03_SKU共用图" -Filter *.png
Add-Type -AssemblyName System.Drawing
foreach ($file in $files) {
    $image = [System.Drawing.Image]::FromFile($file.FullName)
    if ($image.Width -ne 1086 -or $image.Height -ne 1448) {
        throw "Bad dimensions: $($file.FullName)"
    }
    $image.Dispose()
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path ".\Toyota_Land_Cruiser_Tozaroa_最终上架包.zip"))
$mainCount = ($zip.Entries | Where-Object { $_.FullName -like "*01_主图*" }).Count
$fitCount = ($zip.Entries | Where-Object { $_.FullName -like "*02_车型适配图*" }).Count
Write-Output "checked_images=$($files.Count) zip_entries=$($zip.Entries.Count) main_in_zip=$mainCount fit_in_zip=$fitCount backup_exists=$(Test-Path '.\Toyota_Land_Cruiser_旧版备份_20260928')"
$zip.Dispose()
