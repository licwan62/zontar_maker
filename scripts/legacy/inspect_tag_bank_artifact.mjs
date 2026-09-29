import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = "C:/Users/Lenovo/Desktop/ZONTAR_灰色无耳车罩_新项目提示词交接包_v1.0/汽车车罩标签词 - 副本.xlsx";
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
console.log((await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 4000 })).ndjson);
console.log((await workbook.inspect({ kind: "table", maxChars: 30000, tableMaxRows: 120, tableMaxCols: 12, tableMaxCellChars: 200 })).ndjson);
