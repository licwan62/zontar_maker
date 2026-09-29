import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";
import { zontarPaths } from "../_shared/paths.mjs";

const P = zontarPaths("renault_logan");
const packageDir = P.vehicle.package;
const templatePath = P.official_template;
const listingOut = `${P.vehicle.info}/Renault_Logan_Tozaroa_官方上架表.xlsx`;   // binary -> asset store
const csvOut = `${P.vehicle.data_dir}/Renault_Logan_Tozaroa_上架内容.csv`;      // table -> git

const common = [
  "#чехолнаРеноЛоган", "#чехолнаRenaultLogan", "#чехол_для_машины_от_дождя",
  "#чехол_от_снега_и_дождя", "#пылезащитаавто", "#всесезонныйчехол",
  "#чехол_на_кузов", "#уличная_парковка"
];
const sedanTags = [
  "#тент_для_седана", "#чехолдляседана", "#чехол_гараж_для_седана", "#тентдляседана",
  "#Тентседан", "#Чехолнаседан", "#тент_на_седан", "#тентчехолнаавтомобильседан",
  "#зимний_чехол_для_седана", "#чехолтентнаавтомобильседан", "#седан_зимний_чехол",
  "#чехол_для_седана_зимний", "#Чехол_для_седана", "#тентнаседан",
  "#портативный_гараж_на_седан", "#седан_тент_чехол_для_авто", "#седан_чехол_для_авто",
  "#чехол_для_седана", "#чехол_в_гараж_от_пыли", "#защита_кузова_от_пыли",
  "#парковка_зимой"
];
const wagonTags = [
  "#чехол_для_универсала", "#тентдляуниверсала", "#Чехолдляуниверсала", "#Чехолдляавтоуниверсал",
  "#универсальныйавточехол", "#чехол_на_авто_универсальный", "#чехолнаавтоуниверсальный",
  "#тентавтомобиляуниверсальный", "#тентдлямашиныуниверсальный", "#чехол_для_авто_универсальный",
  "#чехолавтомобиляуниверсальный", "#УниверсальноеПокрывало", "#автопокрывало_всесезонное",
  "#чехол_на_машину_всесезонный", "#автомобильный_чехол_на_кузов", "#всесезонныйтент",
  "#Всесезоннаязащита", "#Открытая_парковка", "#парковка_на_улице",
  "#Чехолдлякузоваавтомобиля", "#тентнакузовмашины"
];

const records = [
  {
    sku: "3M", ship: "L", body: "Sedan / Stepway", years: "2004–2022",
    fitment: "Renault Logan Sedan и Stepway 2004–2022",
    title: "Чехол на автомобиль Tozaroa для Renault Logan Sedan и Stepway 2004–2022, серый всесезонный тент на весь кузов машины от дождя, снега, солнца, пыли и листьев, без карманов для зеркал",
    tags: [...common, ...sedanTags],
    bullets: `1. ТОЧНАЯ ПРИВЯЗКА К МОДЕЛИ. Вариант 3M подготовлен для Renault Logan с кузовом седан, включая версию Stepway, годов выпуска 2004–2022. Перед заказом обязательно сверьте модель, тип кузова и год: этот вариант не предназначен для Logan MCV/Wagon.\n2. СПЛОШНАЯ КОНСТРУКЦИЯ БЕЗ КАРМАНОВ ДЛЯ ЗЕРКАЛ. Боковые зеркала складываются перед установкой и остаются под единым полотном. Такая схема сохраняет аккуратный силуэт, уменьшает количество выступающих деталей и подходит для повседневного накрывания автомобиля на парковке.\n3. СЕРЫЙ ОДНОСЛОЙНЫЙ PEVA. Лёгкий гладкий материал помогает закрыть кузов от обычных осадков, снега, солнечного света, дорожной пыли и опавших листьев. Чехол не является утеплителем и не заменяет стационарный гараж; заявленные свойства относятся к бытовой защите припаркованного автомобиля.\n4. ДЛЯ УЛИЦЫ И ГАРАЖА. Полное покрытие кузова помогает поддерживать автомобиль чище между поездками и сокращает прямой контакт лакокрасочного покрытия с пылью и сезонными загрязнениями. Надевайте только на остывший автомобиль и чистую поверхность без острых предметов.\n5. УСТАНОВКА И УХОД. Сначала определите переднюю и заднюю части, сложите зеркала, равномерно расправьте материал по крыше, капоту и багажнику, затем проверьте посадку по периметру. После дождя просушите чехол перед хранением; очищайте мягкой влажной тканью без абразивов.`
  },
  {
    sku: "2M", ship: "L", body: "MCV Wagon", years: "2009–2018",
    fitment: "Renault Logan Wagon и MCV 2009–2018",
    title: "Чехол на автомобиль Tozaroa для Renault Logan MCV Wagon 2009–2018, серый всесезонный тент на весь кузов универсала Logan от дождя, снега, солнца, пыли и листьев, без карманов для зеркал",
    tags: [...common, ...wagonTags],
    bullets: `1. ДЛЯ ДЛИННОГО КУЗОВА MCV. Вариант 2M рассчитан на Renault Logan MCV/Wagon с кузовом универсал 2009–2018 годов. Удлинённая зона крыши и багажного отделения учтена отдельно от седана; перед покупкой проверьте, что у вас именно MCV или Wagon, а не обычный Logan Sedan/Stepway.\n2. НЕПРЕРЫВНОЕ ПОЛОТНО БЕЗ УШЕЙ. Чехол выполнен без наружных карманов для зеркал: зеркала необходимо сложить, после чего единое полотно закрывает боковые зоны. Это формирует спокойную посадку без лишних выступов и облегчает регулярное использование на стоянке.\n3. ЛЁГКИЙ СЕРЫЙ PEVA. Однослойный гладкий материал предназначен для базовой сезонной защиты кузова от дождя, снега, солнечного света, пыли и листьев. Материал не следует воспринимать как утеплённый, стёганый или толстый многослойный чехол; характеристики указаны без завышенных обещаний.\n4. ПОЛНОЕ ПОКРЫТИЕ УНИВЕРСАЛА. Чехол закрывает капот, длинную крышу, боковины и заднюю грузовую часть, помогая сохранить кузов чище при уличной, дворовой или гаражной парковке. Не надевайте изделие на горячий автомобиль и не оставляйте под полотном острые выступающие предметы.\n5. ПРАВИЛЬНАЯ УСТАНОВКА. Разложите чехол рядом с автомобилем, определите перед и зад, сложите зеркала, затем постепенно расправьте материал от крыши к бамперам и проверьте края по всему периметру. После влажной погоды полностью просушите изделие; храните в сухом виде и очищайте без жёстких щёток.`
  }
];

for (const r of records) {
  if (r.title.length > 200) throw new Error(`${r.sku} title too long: ${r.title.length}`);
  if (r.tags.length !== 29 || new Set(r.tags).size !== 29) throw new Error(`${r.sku} tag count/uniqueness error`);
  const tooLong = r.tags.filter(t => t.length > 30);
  if (tooLong.length) throw new Error(`${r.sku} tags over 30: ${tooLong.join(", ")}`);
}

const headers = ["SKU","实际发货尺码","品牌","车型","适配","标题","标题字符数","标签","标签数量","五点介绍","颜色","材质","主图","车型图","共用SKU图"];
const rows = records.map(r => [r.sku,r.ship,"Tozaroa","Renault Logan",r.fitment,r.title,r.title.length,r.tags.join(" "),r.tags.length,r.bullets,"灰色","PEVA",`../01_主图/Renault_Logan_${r.sku}_主图_1086x1448.png`,`../02_车型适配图/Renault_Logan_${r.sku}_车型适配图_1086x1448.png`,`../03_SKU共用图/Renault_Logan_3M_2M_SKU共用选择图_1086x1448.png`]);
const csvEscape = v => `"${String(v).replaceAll('"','""')}"`;
await fs.writeFile(csvOut, "\uFEFF" + [headers, ...rows].map(row => row.map(csvEscape).join(",")).join("\r\n"), "utf8");

const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(templatePath));
const sheet = wb.worksheets.getItem("模板");
for (let i = 0; i < records.length; i++) {
  const r = records[i], row = 13 + i;
  sheet.getRange(`A${row}:AX${row}`).copyFrom(sheet.getRange("A12:AX12"), "all");
  const values = Array(50).fill(null);
  const set = (column, value) => { values[column - 1] = value; };
  set(1, 9 + i); set(2, `RenaultLogan-${r.sku}`); set(3, r.title); set(4, 301); set(5, 888); set(6, "是");
  set(10, 800); set(11, 260); set(12, 60); set(13, 300); set(17, "Tozaroa"); set(18, "RenaultLogan");
  set(19, r.sku); set(20, "灰色"); set(21, "汽车罩"); set(22, 800); set(23, 1); set(24, r.tags.join(" "));
  set(25, r.bullets); set(27, "Renault"); set(29, "Renault"); set(33, r.title); set(34, 1); set(35, "PEVA");
  set(36, "Renault Logan"); set(37, "Без карманов для зеркал"); set(38, "汽车"); set(40, "中国"); set(41, 1);
  sheet.getRange(`A${row}:AX${row}`).values = [values];
}
wb.recalculate();
const preview = await wb.render({ sheetName: "模板", range: "A8:AO15", scale: 0.75, format: "png" });
await fs.writeFile(`${packageDir}/05_预览/Logan_官方上架表预览.png`, new Uint8Array(await preview.arrayBuffer()));
console.log((await wb.inspect({ kind: "region", sheetId: "模板", range: "A13:AO14", maxChars: 18000, tableMaxRows: 4, tableMaxCols: 41, tableMaxCellChars: 180 })).ndjson);
console.log((await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "formula errors" })).ndjson);
await (await SpreadsheetFile.exportXlsx(wb)).save(listingOut);

console.log(JSON.stringify({listingOut,csvOut,records:records.map(r=>({sku:r.sku,titleChars:r.title.length,tags:r.tags.length,bulletChars:r.bullets.length}))},null,2));
