import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "file:///C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";
const input="C:/Users/Lenovo/Desktop/ozon发货/Ozon上架链接汇总_两店对应完成.xlsx";
const root="C:/Users/Lenovo/Desktop/ZONTAR_灰色无耳车罩_新项目提示词交接包_v1.0";
const output=`${root}/Ozon上架链接汇总_Lada2121实际尺码候选.xlsx`;
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(input));
const store=wb.worksheets.getItem("ozon跨境一店");
const total=wb.worksheets.getItem("Ozon上架链接汇总");
const note="按品牌+车型检索销量表：Lada 2121 / Urban / Bronto / Рысь → 自动尺码 YS-380 → OZON尺码 XS → 发货尺码 S";
for (const r of [75,76,77,78,79,80,82]) {
  store.getRange(`L${r}:M${r}`).values=[["YS-380","S"]];
  store.getRange(`AB${r}`).values=[[note]];
}
for (const r of [5,63,64,65,66,67,68,70]) total.getRange(`L${r}:M${r}`).values=[["YS-380","S"]];
wb.recalculate();
const preview=await wb.render({sheetName:"ozon跨境一店",range:"J73:AB82",scale:1,format:"png"});
await fs.writeFile(`${root}/Lada2121_实际尺码预览.png`,new Uint8Array(await preview.arrayBuffer()));
await (await SpreadsheetFile.exportXlsx(wb)).save(output);
console.log(JSON.stringify({output,note},null,2));
