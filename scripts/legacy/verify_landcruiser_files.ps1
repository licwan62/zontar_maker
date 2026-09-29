$candidate = Get-FileHash -Algorithm SHA256 -LiteralPath ".\Ozon上架链接汇总_LandCruiser_写回候选.xlsx"
$original = Get-FileHash -Algorithm SHA256 -LiteralPath "C:\Users\Lenovo\Desktop\ozon发货\Ozon上架链接汇总_两店对应完成.xlsx"
Write-Output "summary_hash_match=$($candidate.Hash -eq $original.Hash)"

$package = ".\Toyota_Land_Cruiser_Tozaroa_最终上架包"
$main = (Get-ChildItem -LiteralPath "$package\01_主图" -Filter *.png).Count
$fit = (Get-ChildItem -LiteralPath "$package\02_车型适配图" -Filter *.png).Count
$selector = (Get-ChildItem -LiteralPath "$package\03_SKU共用图" -Filter *.png).Count
$gallery = (Get-ChildItem -LiteralPath "$package\06_共用越野车副图" -Filter *.png).Count
$pc = (Get-ChildItem -LiteralPath "$package\07_A+_PC端" -Filter *.png).Count
$mobile = (Get-ChildItem -LiteralPath "$package\08_A+_移动端" -Filter *.png).Count
Write-Output "main=$main fit=$fit selector=$selector gallery=$gallery pc=$pc mobile=$mobile"

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path ".\Toyota_Land_Cruiser_Tozaroa_最终上架包.zip"))
$xlsx = ($zip.Entries | Where-Object { $_.FullName -like "*.xlsx" }).Count
Write-Output "zip_files=$($zip.Entries.Count) xlsx_in_zip=$xlsx"
$zip.Dispose()
