# MD／CD 板面彎曲建置進度（2026-09-17）

## 本次完成與界線

MD 是紙張製造的機器方向，CD 是橫向；這裡用兩個方向的板面抗彎剛度，並非把摺痕彈簧改成兩種就宣稱板面彎曲。
分段剛體板件由彈性轉動關節相接。四片蓋各四段，原四個彈塑性摺痕保留，新增十二個板面彎曲關節。
這是沿板條長度的一維方向性代理；沒有完整二維正交異向性殼、耦合扭曲、面內拉伸、壓皺、破裂或材料 FEM。
箱壁與底板仍剛體。主蓋沿 CD、次蓋沿 MD 是明示的紙箱展開方向假設，不是已量測的切紙方向。

## 參考來源與自行實作

- **文獻實測**：[Holmvall，Table 1，130TL B-flute](https://onlinelibrary.wiley.com/doi/full/10.1002/pts.2607)：D_MD=4.26、D_CD=1.84 N·m；面密度403 g/m²；厚度2.78 mm。材料檔 `config/materials/b_flute_130tl.json` 保留來源與 provenance。這個樣本比原需求3–5 mm薄，不能宣稱是同一材質／紙箱。
- **自行建立的離散模型**：梁能量離散得到 k=D×板寬／段長（N·m/rad），夾持板條根部半格使用2k；不是文獻作者的 Isaac Sim 實作。USD 每度剛度換算 k×π/180。
- **自行建立的測試**：零重力隔離板面，以0.03 N·m端力矩載入3秒，卸載3秒；端力矩等價為每個平面關節相同廣義力矩，透過 force drive 參考角偏移施加。不是直接指定實測姿態，也不是机器人碰撞驗證。
- 板面阻尼0.02 N·m·s/rad、分段數、±30°板面關節限位均為代理設定，非材料量測。摺痕參數仍未校準。
- **摺痕研究**：[Mentrasti 等，2013](https://iris.univpm.it/handle/11566/110320)研究0–180°加載／卸載，顯示路徑與壓痕條件相關。已確認摘要，未取得可直接套用的原始力矩－角度資料；研究紙板也不能直接當作本案瓦楞紙箱。

## 原混合載荷失敗是什麼

原測試同時施力，MajorYN 用小力留在關閉附近，卻要求下面兩片次蓋都能開啟且產生塑性角；主蓋的碰撞阻擋造成失敗。
它不是「全部流程失敗」，也不是本次MD/CD理論測試失敗。保留原失敗與原驗收門檻，不用新測試覆蓋成 pass。
分開測摺痕及先主蓋後次蓋的既有診斷已通過；本次16關節紙箱只確認回呼／讀回，不宣稱新紙箱開蓋任務已通過。

## 自行執行與 WebRTC

終端機重跑實際 MD／CD 測試（GPU0先檢查至少8000 MiB可用；私有headless，不占viewer）：

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf-panel-bending-test
./scripts/pf-panel-usd-check --run 20260917T121758Z_ext1_mdcd_bending
```

既有 WebRTC 編輯器先存檔並停止 timeline，Script Editor 執行：

```python
exec(open('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/scripts/carton_mdcd_editor.py').read())
```

等待載入完成，Stage選 `/World/Carton/MajorYN_S3`，按F定位；按Play，控制視窗先開兩片主蓋，再 Shift＋左鍵拉／推最外側板段。每片蓋的可彎曲段為原名及 `_S1`、`_S2`、`_S3`。
載入的是有碰撞與關節的 `asset.usda`，不是動畫錄影；本案不替你按Play，不重啟viewer。
停止會重設自己的塑性歷史，暫停保留；不支援撕裂／揉成一團。這個來源材料板面相當硬，外力小時彎曲幅度可能不明顯。
若只想看MD/CD板條，可停止timeline後載入 `/mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260917T121758Z_ext1_mdcd_bending/coupon_asset.usda`；該檔沒有自動端力矩腳本，直接Play不能重現測試載荷。數值比較請重跑終端測試並看CSV／曲線。

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


## 被動操作需求更新

本文件原先開蓋操作說明由 reports/development/2026-09-17_passive_carton_forces.md 取代；不再提供開／關按鈕。原run與結果保留。原生WebRTC未宣稱修復。
