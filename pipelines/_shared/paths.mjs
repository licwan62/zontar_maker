// Resolve pipeline locations from the Python layout (single source of truth: src/zontar/layout.py).
//   import { zontarPaths } from "../_shared/paths.mjs";
//   const P = zontarPaths("toyota_rav4");   // P.vehicle.package, P.official_template, ...
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

export function zontarPaths(vehicle) {
  const args = ["-m", "zontar", "paths", "--json"];
  if (vehicle) args.push("--vehicle", vehicle);
  const out = execFileSync(process.env.PYTHON || "python", args, {
    cwd: repoRoot,
    encoding: "utf8",
    env: { ...process.env, PYTHONPATH: path.join(repoRoot, "src"), PYTHONIOENCODING: "utf-8" },
  });
  const P = JSON.parse(out);
  for (const dir of [P.listing_summary_candidates, P.reports]) fs.mkdirSync(dir, { recursive: true });
  return P;
}
