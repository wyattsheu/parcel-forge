# 編輯器匯入失敗修正

使用者回報 ModuleNotFoundError: parcel_forge.carton_lifecycle，載入在清理之前中止。檔案本機存在；viewer實際搜尋狀態未取得，不能斷言其根因。
入口現在確認viewer可見檔案、把自有parcel_forge包搜尋路徑／spec指向本專案、invalidate import caches，並取得非同步Task結果，直接顯示traceback。不清空其他模組、不裝套件、不啟用Physics UI。pf_live None時不呼叫close。

./scripts/pf-carton-editor-test exit0，runs/20260917T125101Z_ext1_editor_loader：在私有Kit故意設錯包搜尋路徑，執行真正carton_force_editor.py，async載入成功、視窗建構成功、單片2N外力開蓋成功、同globals第二次載入成功。這不是WebRTC原生滑鼠或人眼驗證。
smoke125024 exit0；syntax與diff檢查在fresh delivery。材料／碰撞／驗收門檻不變。

先存檔並停止timeline，Script Editor重跑：

```python
exec(open('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/scripts/carton_force_editor.py').read())
```

等待載入完成後Play；MajorYN edge force +2N測單片拉力，0放手，負數壓力；Hit按鈕是短脈衝。若前置檢查報Viewer cannot see repository module，代表目前viewer無法讀該路徑，請保留完整錯誤；若成功但原生mouse不動，仍屬另一個未解的問題。
下一個單一動作：使用者在既有viewer重跑新版入口，確認module search與READ-ONLY mouse diagnosis輸出。UI activation前次審查拒絕且使用者尚未批准，仍未執行。
