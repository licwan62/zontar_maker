import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "file:///C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const inputPath="C:/Users/Lenovo/Desktop/ozon发货/Ozon上架链接汇总_两店对应完成.xlsx";
const root="C:/Users/Lenovo/Desktop/ZONTAR_灰色无耳车罩_新项目提示词交接包_v1.0";
const outputPath=`${root}/Ozon上架链接汇总_尺码优化候选.xlsx`;

const edits={
  "ozon跨境一店":[
    [15,"2XL","L"],[152,"2L+","L"],[153,"2XL","L"],[154,"2M","M"],
    [155,"3M-0","L"],[156,"3S-0","M"],[158,"2M","M"],[161,"2L+","L"],
    [162,"2XL","L"],[163,"3M-0","L"],[164,"YL","YL"],[165,"YM+","YM"],
  ],
  "ozon跨境二店":[
    [14,"2XL","L"],[15,"2L+","L"],[16,"2M","M"],[19,"2L+","L"],
    [20,"2XL","L"],[21,"3M-0","L"],[23,"2M","M"],[24,"2L+","L"],
  ],
};

const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(inputPath));
const changedItems=new Map();
for (const [sheetName,rows] of Object.entries(edits)) {
  const ws=wb.worksheets.getItem(sheetName);
  for (const [row,autoSize,shipSize] of rows) {
    const oz=String(ws.getRange(`K${row}`).values[0][0]??"");
    const item=String(ws.getRange(`O${row}`).values[0][0]??"");
    ws.getRange(`L${row}:M${row}`).values=[[autoSize,shipSize]];
    ws.getRange(`AB${row}`).values=[[`按品牌+车型检索销量表：OZON尺码 ${oz} → 自动尺码 ${autoSize} → 发货尺码 ${shipSize}`]];
    if (item) changedItems.set(item,[autoSize,shipSize]);
  }
}

const total=wb.worksheets.getItem("Ozon上架链接汇总");
const totalItems=total.getRange("O2:O138").values.flat().map(v=>String(v??""));
for (let i=0;i<totalItems.length;i++) {
  const mapped=changedItems.get(totalItems[i]);
  if (mapped) total.getRange(`L${i+2}:M${i+2}`).values=[[mapped[0],mapped[1]]];
}
wb.recalculate();
const preview=await wb.render({sheetName:"ozon跨境一店",range:"A148:AB166",scale:1,format:"png"});
await fs.writeFile(`${root}/尺码优化_一店预览.png`,new Uint8Array(await preview.arrayBuffer()));
const out=await SpreadsheetFile.exportXlsx(wb); await out.save(outputPath);
console.log(JSON.stringify({outputPath,editedStore1:edits["ozon跨境一店"].length,editedStore2:edits["ozon跨境二店"].length,totalMatched:[...changedItems.keys()].filter(k=>totalItems.includes(k)).length},null,2));
