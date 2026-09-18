# 即時互動控制器執行證據

這是執行結果，建置進度與操作指令見 ../development/2026-09-17_live_carton_interaction.md。

- ./scripts/pf smoke --physics-only：exit0，20260917T120157Z_s1_smoke。
- 首次測試120517Z_ext1_live_callback_test：rawexit-6，Usd layer weak-pointer fatal；沒有result，不能稱執行通過。保持載入Stage強參照後不再發生此錯誤，舊log保留。
- 120600Z_ext1_live_callback_test：raw0、1208次PRE物理回呼，兩主蓋plastic reference約.810396rad，pass；native mouse/UI not_tested。
- ./scripts/pf-carton-live-test：exit0，120721Z_ext1_live_callback_test；回呼、施力矩、塑性讀回pass，面板建構headless執行完成。
- 逐步readback／施力事件：120735Z_ext1_live_interaction/events.jsonl。

各headless測試前保存GPU庫存，livestream disabled；沒有對既有WebRTC執行載入／播放／關閉。
真正Shift滑鼠、操作面板可見性、相機render及WebRTC human viewing仍not_tested。
固定箱體、剛性板面、未校準材料模型的限制不變；並未新增捶凹／破裂模型。
