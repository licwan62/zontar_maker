import fs from "node:fs/promises";
import { Workbook } from "@oai/artifact-tool";

const path = "C:/Users/Lenovo/Desktop/ZONTAR_灰色无耳车罩_新项目提示词交接包_v1.0/Toyota_RAV4_Tozaroa_最终上架包/04_上架资料/Toyota_RAV4_Tozaroa_上架内容.csv";
const text = (await fs.readFile(path, "utf8")).replace(/^\uFEFF/, "");
const wb = await Workbook.fromCSV(text, { sheetName: "RAV4" });
const sh = wb.worksheets.getItem("RAV4");
const rows = sh.getRange("A2:N4").values;
const result = rows.map(r => {
  const list = String(r[6]).trim().split(/\s+/);
  return {
    sku: r[0],
    storedTagCount: Number(r[7]),
    actualTagCount: list.length,
    uniqueTagCount: new Set(list).size,
    maxTagLength: Math.max(...list.map(t => [...t].length)),
    fivePointsPresent: ["1.", "2.", "3.", "4.", "5."].every(x => String(r[8]).includes(x)),
    fivePointLength: [...String(r[8])].length,
    titleChars: [...String(r[4])].length,
    mainImage: r[11],
    fitmentImage: r[12],
    selectorImage: r[13]
  };
});
console.log(JSON.stringify(result, null, 2));
if (result.some(r => r.storedTagCount !== 29 || r.actualTagCount !== 29 || r.uniqueTagCount !== 29 || r.maxTagLength > 30 || !r.fivePointsPresent)) process.exit(1);
