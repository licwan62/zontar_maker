import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";
const path = "C:/Users/Lenovo/Desktop/ZONTAR_灰色无耳车罩_新项目提示词交接包_v1.0/汽车车罩标签词 - 副本.xlsx";
const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(path));
for (const term of ["logan|логан|renault|рено", "седан|универсал|wagon|mcv", "дожд|снег|солнц|пыл", "парков|кузов|всесезон"]) {
  console.log((await wb.inspect({kind:"match", searchTerm:term, options:{useRegex:true,maxResults:100}, maxChars:12000})).ndjson);
}
