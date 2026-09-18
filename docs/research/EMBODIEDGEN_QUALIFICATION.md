# 首個圖片生成 provider：資格測試卡

Status: planned；本卡不是已安裝／已跑過。候選 upstream：https://github.com/HorizonRobotics/EmbodiedGen。
父計畫：docs/plans/2026-09-18_general_asset_workflow_master_plan.md P3a。先只測單物件，不導入場景／訓練服務。

1. 選固定 tag/commit，保存 README、LICENSE、CLI --help 與 hash；分別確認 code、權重、資料與後端依賴授權。
2. 選其中一個已支援的圖片後端，記 model/version；不推定 TRELLIS 和 TRELLIS.2 相同。先盤點已有模型快取和隔離環境。
3. 不規則剛性物件輸入需照片／來源授權、可靠尺度、任務 brief。透明包材不作第一例。
4. 隔離環境、檔案交接；不得改 Isaac venv／driver。保存 setup 耗時和需求；外部 provider 不可用即 blocked。
5. 呼叫無人值守入口，保存 request、stdout/stderr、exit、時間、VRAM、產物 hash；重試預算三次，原始失敗不覆蓋。
6. 記 geometry、parts、material、URDF/mesh 輸出是否真正存在；質量／摩擦 VLM 推估標 assumed，不當真值。
7. 透過本機可用的 USD 匯入路徑驗尺度、碰撞 proxy、mass/COM/inertia、material；不能僅憑 export 字樣宣稱相容。
8. 在新 run 驗落地、有限狀態與接觸受力；此時才確認本機能力。不能暗改材料提升穩定。
9. 新目錄冷載入、WebRTC 真入口、小操作與人工確認另列；用户睡覺時 human_webrtc=not_tested。
10. 對照相同需求的已有資產／參數化路徑，報第一輪結果、修復成本和能力覆蓋。可用後才選預設。

資格門檻：必要依賴與權重可用、公司用途授權可接受、隔離不影響主線、實際產物可匯入並通過該剛體 scope 的必要測試。
未知量（權重下載成本、本機效能、轉換保真）在實跑前保持 unknown。不要安裝全部後端来猜哪個可以用。
