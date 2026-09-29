# Legacy one-off scripts (2026-09-16 … 09-29)

Kept for reference only. They were written on the original author's machine and
still point at `C:\Users\Lenovo\Desktop\...` and at the old flat folder layout,
so they will not run as-is. `manifests/migration_map.csv` maps every old file
path to its new location if you need to revive one.

| Group | Files | What they did |
|---|---|---|
| RAV4 design iterations | build_rav4_package / _redesign / _v3 / _v4 | V1–V5 images, superseded by `pipelines/toyota_rav4/10_build_images_v6.py` |
| Summary workbook edits | sync_listing_info, optimize_size_mapping_artifact, update_rav4_ys_actual, fix_lada2121_actual | write-back candidates of Ozon上架链接汇总 (see data/listing_summary/snapshots) |
| Size-mapping research | aggregate_size_mapping, audit_summary_sizes, match_brand_model_sizes, lookup_* | queries against 俄罗斯带销量数据 (now data/reference/ru_sales_0928) |
| Inspection / QA | inspect_*, search_*, compare_workbooks, help_artifact_csv | exploratory reads of workbooks |
| Verification | verify_* | before/after checks of each write-back |
