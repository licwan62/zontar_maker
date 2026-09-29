import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";
import { zontarPaths } from "../_shared/paths.mjs";

const P = zontarPaths("toyota_rav4");
const root = P.reports;  // QA previews land in outputs/reports
const csvPath = `${P.vehicle.data_dir}/Toyota_RAV4_Tozaroa_上架内容.csv`;
const templatePath = P.official_template;
const summaryBasePath = P.listing_summary;
const templateOut = `${P.vehicle.info}/Toyota_RAV4_Tozaroa_官方上架表.xlsx`;
const summaryOut = `${P.listing_summary_candidates}/Ozon上架链接汇总_RAV4_候选.xlsx`;

function parseCsv(text) {
  const rows=[]; let row=[], field="", quoted=false;
  for (let i=0;i<text.length;i++) {
    const ch=text[i];
    if (quoted) {
      if (ch==='"' && text[i+1]==='"') { field+='"'; i++; }
      else if (ch==='"') quoted=false;
      else field+=ch;
    } else {
      if (ch==='"') quoted=true;
      else if (ch===',') { row.push(field); field=""; }
      else if (ch==='\n') { row.push(field.replace(/\r$/, "")); rows.push(row); row=[]; field=""; }
      else field+=ch;
    }
  }
  if (field.length || row.length) { row.push(field); rows.push(row); }
  const headers=rows.shift().map((h,i)=>i===0?h.replace(/^\uFEFF/,""):h);
  return rows.filter(r=>r.some(Boolean)).map(r=>Object.fromEntries(headers.map((h,i)=>[h,r[i]??""])));
}

const records=parseCsv(await fs.readFile(csvPath,"utf8"));
if (records.length!==3) throw new Error(`Expected 3 RAV4 rows, got ${records.length}`);

const template = await SpreadsheetFile.importXlsx(await FileBlob.load(templatePath));
const ts = template.worksheets.getItem("模板");
for (let i=0;i<records.length;i++) {
  const r=records[i], row=10+i;
  ts.getRange(`A${row}:AX${row}`).copyFrom(ts.getRange("A9:AX9"), "all");
  const vals=Array(50).fill(null);
  const set=(col,val)=>{ vals[col-1]=val; };
  set(1,6+i); set(2,`ToyotaRAV4-${r.SKU}`); set(3,r.标题); set(4,301); set(5,888); set(6,"是");
  set(10,800); set(11,260); set(12,60); set(13,300);
  set(17,"Tozaroa"); set(18,"ToyotaRAV4"); set(19,r.SKU); set(20,"灰色"); set(21,"汽车罩");
  set(22,800); set(23,1); set(24,r.标签); set(25,r.五点介绍); set(27,"Toyota"); set(29,"Toyota");
  set(33,r.标题); set(34,1); set(35,"PEVA"); set(36,"Toyota RAV4"); set(37,"Без карманов для зеркал");
  set(38,"汽车"); set(40,"中国"); set(41,1);
  ts.getRange(`A${row}:AX${row}`).values=[vals];
}
template.recalculate();
const tprev=await template.render({sheetName:"模板",range:"A2:AO12",scale:0.8,format:"png"});
await fs.writeFile(`${root}/RAV4_官方模板_预览.png`,new Uint8Array(await tprev.arrayBuffer()));
await (await SpreadsheetFile.exportXlsx(template)).save(templateOut);

const summary = await SpreadsheetFile.importXlsx(await FileBlob.load(summaryBasePath));
const store=summary.worksheets.getItem("ozon跨境一店");
const total=summary.worksheets.getItem("Ozon上架链接汇总");
for (let i=0;i<records.length;i++) {
  const r=records[i], row=164+i;
  store.getRange(`A${row}:AB${row}`).copyFrom(store.getRange("A163:AB163"),"all");
  const vals=Array(28).fill(null);
  vals[0]=163+i; vals[1]="定制低价分尺码TOYOTA RAV4"; vals[2]="ToyotaRAV4"; vals[3]=r.标题;
  vals[5]="Toyota"; vals[6]="Toyota-RAV4"; vals[7]="Toyota"; vals[8]="30*26*6"; vals[9]="0.8kg";
  vals[10]=r.SKU; vals[11]=r.SKU; vals[12]=r.SKU; vals[14]=`ToyotaRAV4-${r.SKU}`;
  vals[15]="单层PEVA（灰色无耳）"; vals[16]=r.适配; vals[17]="越野车"; vals[19]=r.标签; vals[20]=r.五点介绍;
  vals[21]=301; vals[23]=301; vals[24]=888; vals[25]="普通PEVA款"; vals[26]="新上架表已并入一店";
  vals[27]="用户提供尺码：M、S；无可用尺码统一归YS";
  store.getRange(`A${row}:AB${row}`).values=[vals];
  total.getRange(`A${136+i}:Y${136+i}`).copyFrom(store.getRange(`A${row}:Y${row}`),"all");
  total.getRange(`A${136+i}`).values=[[135+i]];
}
summary.recalculate();
const sprev=await summary.render({sheetName:"Ozon上架链接汇总",range:"A132:Y138",scale:1,format:"png"});
await fs.writeFile(`${root}/RAV4_汇总表_预览.png`,new Uint8Array(await sprev.arrayBuffer()));
await (await SpreadsheetFile.exportXlsx(summary)).save(summaryOut);

console.log(JSON.stringify({templateOut,summaryOut,skus:records.map(r=>r.SKU)},null,2));
