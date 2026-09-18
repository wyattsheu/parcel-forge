# 工作流執行回報：正常／缺底 bridge suite

- 20260917T000053Z_s2_open_box_normal → runs/20260917T012259Z_s5b_upstream_bridge：task=pass，exit=0，upstream=pass。
- 20260917T000039Z_s2_open_box_no_bottom → runs/20260917T012301Z_s5b_upstream_bridge：task=fail，exit=1，upstream=pass。
- 20260917T012407Z_s2_open_box_normal → runs/20260917T012506Z_s5b_upstream_bridge：task=pass，exit=0，upstream=pass。
- 20260917T012420Z_s2_open_box_no_bottom → runs/20260917T012508Z_s5b_upstream_bridge：task=fail，exit=1，upstream=pass。

詳細判定與 original reports 在各 run 的 bridge_result.json 與 upstream/。
模擬原始量測位於 source_run；adapter 本身不重跑物理或 rendering。
缺底 task fail 是預期拒絕。WebRTC 尚無人工確認，影片尚未產生。
指令與來源見 reports/development/2026-09-17_s5b_evidence_bridge.md。
