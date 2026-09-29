import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "file:///C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const input="C:/Users/Lenovo/Desktop/ozon发货/Ozon上架链接汇总_两店对应完成.xlsx";
const root="C:/Users/Lenovo/Desktop/ZONTAR_灰色无耳车罩_新项目提示词交接包_v1.0";
const output=`${root}/Ozon上架链接汇总_RAV4实际检索候选.xlsx`;
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(input));
const note="按品牌+车型实际检索：RAV4三门2000–2006为OZON S、自动尺码YS-410、发货YM；1994–2000短轴三门为OZON XS、自动尺码YS-380、发货S。当前合并条目按覆盖更多年份的S→YM。";
const store=wb.worksheets.getItem("ozon跨境一店");
store.getRange("K166:N166").values=[["S","YS-410","YM",note]];
store.getRange("AB166").values=[[note]];
const total=wb.worksheets.getItem("Ozon上架链接汇总");
total.getRange("K138:N138").values=[["S","YS-410","YM",note]];
wb.recalculate();
const preview=await wb.render({sheetName:"ozon跨境一店",range:"A162:AB166",scale:1,format:"png"});
await fs.writeFile(`${root}/RAV4_YS实际检索预览.png`,new Uint8Array(await preview.arrayBuffer()));
await (await SpreadsheetFile.exportXlsx(wb)).save(output);
console.log(JSON.stringify({output,note},null,2));
