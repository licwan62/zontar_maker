import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";
import { zontarPaths } from "../_shared/paths.mjs";

const P = zontarPaths("toyota_land_cruiser");
const packageDir = P.vehicle.package;
const csvPath = `${P.vehicle.data_dir}/Toyota_Land_Cruiser_Tozaroa_上架内容.csv`;
const templatePath = P.official_template;
const listingOut = `${P.vehicle.info}/Toyota_Land_Cruiser_Tozaroa_官方上架表.xlsx`;
const summaryPath = P.listing_summary;
const summaryCandidate = `${P.listing_summary_candidates}/Ozon上架链接汇总_LandCruiser_写回候选.xlsx`;

function parseCsv(text) {
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (ch === '"') quoted = false;
      else field += ch;
    } else {
      if (ch === '"') quoted = true;
      else if (ch === ',') { row.push(field); field = ""; }
      else if (ch === '\n') { row.push(field.replace(/\r$/, "")); rows.push(row); row = []; field = ""; }
      else field += ch;
    }
  }
  if (field.length || row.length) { row.push(field); rows.push(row); }
  const headers = rows.shift().map((h, i) => i === 0 ? h.replace(/^\uFEFF/, "") : h);
  return rows.filter(r => r.some(Boolean)).map(r => Object.fromEntries(headers.map((h, i) => [h, r[i] ?? ""])));
}

const records = parseCsv(await fs.readFile(csvPath, "utf8"));
if (records.length !== 4) throw new Error(`Expected 4 Land Cruiser records, got ${records.length}`);

// Create the model-specific upload workbook from the official template.
const listing = await SpreadsheetFile.importXlsx(await FileBlob.load(templatePath));
const listingSheet = listing.worksheets.getItem("模板");
const startListingRow = 13;
for (let i = 0; i < records.length; i++) {
  const record = records[i];
  const row = startListingRow + i;
  listingSheet.getRange(`A${row}:AX${row}`).copyFrom(listingSheet.getRange("A12:AX12"), "all");
  const values = Array(50).fill(null);
  const set = (column, value) => { values[column - 1] = value; };
  set(1, 9 + i);
  set(2, `ToyotaLandCruiser-${record.SKU}`);
  set(3, record.标题);
  set(4, 301);
  set(5, 888);
  set(6, "是");
  set(10, 800);
  set(11, 260);
  set(12, 60);
  set(13, 300);
  set(17, "Tozaroa");
  set(18, "ToyotaLandCruiser");
  set(19, record.SKU);
  set(20, "灰色");
  set(21, "汽车罩");
  set(22, 800);
  set(23, 1);
  set(24, record.标签);
  set(25, record.五点介绍);
  set(27, "Toyota");
  set(29, "Toyota");
  set(33, record.标题);
  set(34, 1);
  set(35, "PEVA");
  set(36, "Toyota Land Cruiser");
  set(37, "Без карманов для зеркал");
  set(38, "汽车");
  set(40, "中国");
  set(41, 1);
  listingSheet.getRange(`A${row}:AX${row}`).values = [values];
}
listing.recalculate();
const listingPreview = await listing.render({ sheetName: "模板", range: "A8:AO16", scale: 0.75, format: "png" });
await fs.writeFile(`${packageDir}/05_预览/LandCruiser_官方上架表预览.png`, new Uint8Array(await listingPreview.arrayBuffer()));
const listingCheck = await listing.inspect({ kind: "region", sheetId: "模板", range: "A13:AO16", maxChars: 16000, tableMaxRows: 6, tableMaxCols: 41, tableMaxCellChars: 140 });
console.log(listingCheck.ndjson);
const listingErrors = await listing.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "listing formula errors" });
console.log(listingErrors.ndjson);
await (await SpreadsheetFile.exportXlsx(listing)).save(listingOut);

// Append the four links to store one and the consolidated summary.
const summary = await SpreadsheetFile.importXlsx(await FileBlob.load(summaryPath));
const store = summary.worksheets.getItem("ozon跨境一店");
const total = summary.worksheets.getItem("Ozon上架链接汇总");
const existingKeys = new Set(store.getRange("O2:O166").values.flat().filter(Boolean).map(String));
for (const record of records) {
  const key = `ToyotaLandCruiser-${record.SKU}`;
  if (existingKeys.has(key)) throw new Error(`Duplicate item number: ${key}`);
}

const autoSize = { S: "YM+", M: "YL", L: "YXL", XL: "YXXL" };
const lookupNote = {
  S: "按品牌+车型实际检索：OZON尺码 S → 自动尺码 YM+ → 实际发货YM；适用71及70 Series短轴。",
  M: "按品牌+车型实际检索：OZON尺码 M → 自动尺码 YL → 实际发货YL；适用60 Series及早期80 Series。",
  L: "按品牌+车型实际检索：OZON尺码 L → 自动尺码 YXL → 实际发货YXL；适用76、80改款、100/200/300、Cygnus及Arctic Trucks。",
  XL: "按品牌+车型实际检索：OZON尺码 XL → 自动尺码 YXXL → 实际发货YXL；适用78及70 Series长轴。",
};

for (let i = 0; i < records.length; i++) {
  const record = records[i];
  const row = 167 + i;
  store.getRange(`A${row}:AB${row}`).copyFrom(store.getRange("A166:AB166"), "all");
  const values = Array(28).fill(null);
  values[0] = 166 + i;
  values[1] = "定制低价分尺码TOYOTA LAND CRUISER";
  values[2] = "ToyotaLandCruiser";
  values[3] = record.标题;
  values[5] = "Toyota";
  values[6] = "Toyota-LandCruiser";
  values[7] = "Toyota";
  values[8] = "30*26*6";
  values[9] = "0.8kg";
  values[10] = record.SKU;
  values[11] = autoSize[record.SKU];
  values[12] = record.实际发货尺码;
  values[14] = `ToyotaLandCruiser-${record.SKU}`;
  values[15] = "单层PEVA（灰色无耳）";
  values[16] = record.适配;
  values[17] = "越野车";
  values[19] = record.标签;
  values[20] = record.五点介绍;
  values[21] = 301;
  values[23] = 301;
  values[24] = 888;
  values[25] = "普通PEVA款";
  values[26] = "新上架表已并入一店";
  values[27] = lookupNote[record.SKU];
  store.getRange(`A${row}:AB${row}`).values = [values];

  const totalRow = 139 + i;
  total.getRange(`A${totalRow}:Y${totalRow}`).copyFrom(store.getRange(`A${row}:Y${row}`), "all");
  total.getRange(`A${totalRow}`).values = [[138 + i]];
}
summary.recalculate();
const summaryPreview = await summary.render({ sheetName: "Ozon上架链接汇总", range: "A135:Y142", scale: 0.85, format: "png" });
await fs.writeFile(`${packageDir}/05_预览/LandCruiser_链接汇总同步预览.png`, new Uint8Array(await summaryPreview.arrayBuffer()));
const summaryCheck = await summary.inspect({ kind: "region", sheetId: "Ozon上架链接汇总", range: "A139:Y142", maxChars: 18000, tableMaxRows: 6, tableMaxCols: 25, tableMaxCellChars: 160 });
console.log(summaryCheck.ndjson);
const summaryErrors = await summary.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "summary formula errors" });
console.log(summaryErrors.ndjson);
await (await SpreadsheetFile.exportXlsx(summary)).save(summaryCandidate);

console.log(JSON.stringify({ listingOut, summaryCandidate, skus: records.map(r => `${r.SKU}->${r.实际发货尺码}`) }, null, 2));
