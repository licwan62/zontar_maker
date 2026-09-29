import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "file:///C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const inputPath = "C:/Users/Lenovo/Desktop/ozon发货/Ozon上架链接汇总_两店对应完成.xlsx";
const outputPath = "C:/Users/Lenovo/Desktop/ZONTAR_灰色无耳车罩_新项目提示词交接包_v1.0/Ozon上架链接汇总_两店对应完成_待写回.xlsx";
const beforePng = "C:/Users/Lenovo/Desktop/ZONTAR_灰色无耳车罩_新项目提示词交接包_v1.0/同步前_汇总尾部.png";
const afterPng = "C:/Users/Lenovo/Desktop/ZONTAR_灰色无耳车罩_新项目提示词交接包_v1.0/同步后_汇总尾部.png";

const input = await FileBlob.load(inputPath);
const wb = await SpreadsheetFile.importXlsx(input);
const source = wb.worksheets.getItem("ozon跨境一店");
const target = wb.worksheets.getItem("Ozon上架链接汇总");

const before = await wb.render({
  sheetName: "Ozon上架链接汇总",
  range: "A128:Y135",
  scale: 1,
  format: "png",
});
await fs.writeFile(beforePng, new Uint8Array(await before.arrayBuffer()));

const sourceValues = source.getRange("A159:Y163").values;
const existingKeys = new Set(target.getRange("O2:O135").values.flat().filter(Boolean).map(String));
const newKeys = sourceValues.map(row => String(row[14] ?? ""));
const duplicates = newKeys.filter(key => existingKeys.has(key));
if (duplicates.length) throw new Error(`目标汇总中已存在货号: ${duplicates.join(", ")}`);

target.getRange("A136:Y140").copyFrom(source.getRange("A159:Y163"), "all");
target.getRange("A136:A140").values = [[135], [136], [137], [138], [139]];

wb.recalculate();

const after = await wb.render({
  sheetName: "Ozon上架链接汇总",
  range: "A133:Y140",
  scale: 1,
  format: "png",
});
await fs.writeFile(afterPng, new Uint8Array(await after.arrayBuffer()));

const check = await wb.inspect({
  kind: "region",
  sheetId: "Ozon上架链接汇总",
  range: "A136:Y140",
  maxChars: 12000,
  tableMaxRows: 10,
  tableMaxCols: 25,
  tableMaxCellChars: 100,
});
console.log(check.ndjson);

const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(outputPath);
console.log(JSON.stringify({ outputPath, beforePng, afterPng, newKeys }, null, 2));
