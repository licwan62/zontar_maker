import fs from "node:fs/promises";
import { Workbook } from "@oai/artifact-tool";

const inputPath = "C:/Users/Lenovo/Desktop/ZONTAR_灰色无耳车罩_新项目提示词交接包_v1.0/Toyota_RAV4_Tozaroa_最终上架包/04_上架资料/Toyota_RAV4_Tozaroa_上架内容.csv";
const csvText = await fs.readFile(inputPath, "utf8");
const workbook = await Workbook.fromCSV(csvText, { sheetName: "RAV4" });
const sheet = workbook.worksheets.getItem("RAV4");
const used = sheet.getUsedRange();
console.log((await workbook.inspect({
  kind: "table",
  sheetId: sheet.sheetId,
  range: used.address,
  include: "values,formulas",
  tableMaxRows: 12,
  tableMaxCols: 20,
  tableMaxCellChars: 1200,
  maxChars: 18000,
})).ndjson);
const preview = await workbook.render({ sheetName: "RAV4", range: used.address, scale: 0.7, format: "png" });
await fs.writeFile("C:/Users/Lenovo/Desktop/ZONTAR_灰色无耳车罩_新项目提示词交接包_v1.0/rav4_csv_before.png", new Uint8Array(await preview.arrayBuffer()));
