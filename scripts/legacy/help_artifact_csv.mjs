import { Workbook } from "@oai/artifact-tool";
const wb = Workbook.create();
wb.worksheets.add("Sheet1");
console.log(wb.help("export csv", { search: "exportCsv|toCSV|csv", include: "index,examples,notes", maxChars: 5000 }).ndjson);
