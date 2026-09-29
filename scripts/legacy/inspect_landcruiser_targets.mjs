import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const files = [
  "C:/Users/Lenovo/Desktop/汽车罩官方上架模板.xlsx",
  "C:/Users/Lenovo/Desktop/ozon发货/Ozon上架链接汇总_两店对应完成.xlsx",
];

for (const file of files) {
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(file));
  console.log(`FILE ${file}`);
  console.log((await wb.inspect({kind:"sheet",include:"id,name",maxChars:5000})).ndjson);
  for (const name of file.includes("官方") ? ["模板"] : ["ozon跨境一店","ozon跨境二店","Ozon上架链接汇总"]) {
    const sh = wb.worksheets.getItem(name);
    const used = sh.getUsedRange();
    console.log(`SHEET ${name} USED ${used?.address ?? "n/a"}`);
    const endRow = used?.rowCount ?? 30;
    const start = Math.max(1,endRow-8);
    const range = name === "模板" ? `A${start}:AX${endRow}` : `A${start}:AB${endRow}`;
    console.log((await wb.inspect({kind:"region",sheetId:name,range,maxChars:12000,tableMaxRows:12,tableMaxCols:30,tableMaxCellChars:120})).ndjson);
    const png = await wb.render({sheetName:name,range,scale:0.65,format:"png"});
    const safe = name.replace(/[^A-Za-z0-9\u4e00-\u9fff]/g,"_");
    await fs.writeFile(`inspect_${safe}.png`,new Uint8Array(await png.arrayBuffer()));
  }
}
