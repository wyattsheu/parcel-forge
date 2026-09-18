# 工作流建置回報：S5-B 正常／缺底轉接驗證

日期：2026-09-17；狀態：done (verified)。

新增薄 adapter `src/parcel_forge/upstream_bridge.py` 與 `pf upstream-check`，
呼叫既有 NVIDIA Validation Agent physics_sane；沒有另建 workflow scheduler。
ITRI place_object_inside 是獨立必需 gate，從 CSV 重新計算，而非複製回歸 pass。
上游尚未執行本案 physical_behavior template；本階段沒有偽造 refine approval。

## 結果

| 案例 | 官方 physics_sane | 模擬執行 | ITRI 放置任務 | 故障回歸 |
| --- | --- | --- | --- | --- |
| 正常箱 | pass | pass | pass（inside） | pass |
| 缺底箱 | pass | pass | fail（fell_through） | pass（正確抓到故障） |

舊 run 與兩次新 run 均得到上述結果。新增五項測試涵蓋正常、故障回歸 pass 不可
升級資產、CSV hash 變更、profile 與原 manifest 不符、缺量測；111 tests，7 skipped。
第一輪測試 fixture 使用錯誤 fault 名稱，已改正並保留失敗 log；未更動 acceptance profile。

證據：
- 舊資料：runs/20260917T012259Z_s5b_upstream_bridge/、runs/20260917T012301Z_s5b_upstream_bridge/。
- 新模擬：runs/20260917T012407Z_s2_open_box_normal/、runs/20260917T012420Z_s2_open_box_no_bottom/。
- 完整離線測試：runs/20260917T012428Z_s5b_bridge_tests/。
- 新轉接結果：見 runs/20260917T012612Z_s5b_completion/bridge_suite.json。

## 自行確認

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf upstream-check --run 20260917T012407Z_s2_open_box_normal
./scripts/pf upstream-check --run 20260917T012420Z_s2_open_box_no_bottom
python3 -m unittest tests.test_upstream_bridge -v
```

正常指令 exit 0；缺底指令預期 exit 1（任務拒絕，並非工具壞掉）。
每次產生新 run，保存 frozen inputs、hashes、官方 request／plan／result、ITRI 判定。
缺資料或修改 snapshot 會拒絕；hash 防護從 adapter 首次讀取封存後開始，
不宣稱可證明未綁定的歷史 CSV 在此前從未被修改。

WebRTC 須逐個執行，看完按 Ctrl+C 再換下一個：

```bash
./scripts/pf view --run 20260917T012407Z_s2_open_box_normal --scene scene_final.usda --ui
./scripts/pf view --run 20260917T012420Z_s2_open_box_no_bottom --scene scene_final.usda --ui
```

預期正常 probe 在箱內底，缺底 probe 在世界地板且低於箱體。
這是最終場景與 viewer 新物理，不是當次運動重播；人工確認仍 not_tested。
本階段未錄製影片；下一張 S5-C 卡處理 exact trajectory 與 MP4。

## 來源

- NVIDIA 0.6.0、SHA a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa 的
  world_understanding/validation/templates.py 與 Validation Agent CLI。
- src/parcel_forge/validation/outcome.py：既有 ITRI local-frame 判定，門檻保持不變。
- 三種結果分離、CSV 再計算與薄轉接為本專案設計；不是 NVIDIA 認證規格。
