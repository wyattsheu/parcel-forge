# MD/CD 實際運行紀錄

## 證據

- physics／readback：`runs/20260917T121758Z_ext1_mdcd_bending/result.json`（host exit0）。MD下彎2.88047 mm、CD6.42617 mm；理論相對誤差2.2634%／1.4305%；卸載末端偏移0.09818／0.03093 mm，MD接近0.1 mm門檻，仍需時間步／分段收斂研究。
- 新紙箱16 DOF，回呼968步，無回呼錯誤；僅接線／執行驗證，非材料與開箱任務驗證。
- NVIDIA USD驗證 `runs/20260917T121839Z_ext1_panel_usd_check/`：41規則、0 failures；自訂16關節／21碰撞板件／剛度單位通過。不是SimReady認證。
- 離線 `runs/20260917T121906Z_ext1_mdcd_offline_checks/`：136 tests，7 skipped，exit0。
- 初次121636案例：板條通過後整合exception，但結果被寫成pass且host0；此整輪應判失敗。程式已修正except一律fail；舊run保留，不可引用其整輪pass。121714整合失敗host1，亦保留。
- 最新 smoke `runs/20260917T121049Z_s1_smoke/` exit0。
- 曲線（CSV生成，非相機影像）：[20260917T122021Z_ext1_mdcd_delivery/mdcd_curve.svg](/mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260917T122021Z_ext1_mdcd_delivery/mdcd_curve.svg)。本輪未渲染、未生成影片；WebRTC人眼與原生滑鼠互動 `not_tested`。

## 校準下一步

文獻能提供板面D／面密度／厚度的有來源起始值，不能校準本箱摺痕Y／阻尼／塑性黏度／疲勞。
先確認紙箱等級、厚度、含水／環境與MD/CD裁切方向；量MD/CD彎曲並記錄夾具跨度，再量各摺痕的力矩－角度加卸載、放手角與多次循環。將擬合資料和保留驗證資料分開。
下一個單一任務：固定材料與載荷，完成 dt 與板段數敏感性比較，保留現有5%及0.1mm門檻。
