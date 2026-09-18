# 交付盤點與正常使用入口／出口

結論：紙箱裝鍵盤的受力開蓋／整箱移動原型已具歷史實測，使用者本次表示畫面不錯。泛用工作流未完整：需求 JSON 預檢與固定程式設定的生成腳本尚未串接。此回報不是新物理測試或完整人工驗收。

## 目前真正可用的入口

1. 生成／測試唯一鍵盤包裹：
```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf-keyboard-package
```
它依 keyboard_package.py 內的尺寸／質量設定生成，沒有讀取 workflow bundle；並非文字或圖片生成入口。
2. 需求預檢（獨立，不會自動接上生成器）：
```bash
./scripts/pf-workflow-preflight contracts/workflow/examples/carton_keyboard.json
```
此範例仍含 null 參數和未支援的 payload_extraction，預期拒絕交付；不要以另一支生成器的局部 pass 當作此需求已通過。
3. 觀看現有合格移動案例，先儲存工作並 Stop，在既有 WebRTC Script Editor：
```python
from pathlib import Path
p = Path("/mnt/HDD4/wyattsheu/ITRI/parcel-forge/scripts/keyboard_package_editor.py")
exec(compile(p.read_text(), str(p), "exec"), globals())
```
載入器自動找 status=pass 且 mobility_verified=true 的 run，使用 asset.usda 與 repo 中的 LiveCarton。按 Play 後受力操作。

## 目前的出口

每次輸出到 runs/<timestamp>_keyboard_package/：
- asset.usda：初始幾何／剛體／關節；需搭配 runtime 才有塑性摺痕。
- config.json：紙箱與摺痕設定；鍵盤幾何尺寸和質量目前仍硬寫程式，尚未完整納入此檔。
- scene_final.usda：測試終態的 USD 匯出；未驗完整物理狀態續跑，不能當成 checkpoint。
- result.json：本次檢查、位置／角度／質量、移動證據及未測項；status=pass 僅涵蓋該腳本的七項檢查。
- runtime.log、launch.json、gpu_inventory.json、code_hashes.json：執行證據。

目前可參考 run：runs/20260918T001602Z_keyboard_package。
exports/carton_v1 是先前紙箱包，不是這次鍵盤包裹的可攜交付包。移交他人／Isaac Lab 仍須整合相依程式與測試。

## 最值得補的缺口（依優先順序）

P0 入口接通：讓生成器讀同一 approved contract，保存 contract/profile/input hashes，機器與人工結果綁到相同產物。現在預檢和生成命令可以分開執行，尚不能宣稱所有生成都被 gate 保護。
P0 交付可靠性：初始 asset.usda 在 configure_physics 前匯出，cold loader 需確認與 headless 的 dt/solver/gravity 一致；保存完整 keyboard config、runtime、狀態和相依檔，測可移動目錄載入。
P1 同例取出：在同一鍵盤包裹做接觸與取出、碰撞穿透檢查，不能只以中心留在箱內證明碰撞完整。
P1 驗證精度：目前有限性只檢查少數取樣點；mobility_verified 雖固定寫 true 但 loader 還要求整體 pass。改為直接由對應 checks 推導並綁 hash 更清楚。任意間接静態錨定分析尚缺。
P1 材料可信度：摩擦尚有 simulator default，摺痕為推導／估計；显式材料後再校準。剛性板無壓凹／破壞，按鍵無行程，不把未建能力當 bug。
P2 泛用生成：來源檢索、自然語言補全、圖片後端實際資格測試；目前尚未完成。不要為了外觀細節延後前面的入口與交付修正。

## 最終預定介面（尚未實作）

入口：文字／圖片／CAD＋任務 → 統一 contract → generation/validation。
出口：可移動資產包（USD＋全部設定＋必要 runtime＋manifest＋結果＋WEBRTC.md），另存 append-only runs。
此處不列尚不存在的 CLI 當成可執行命令。

來源：[NVIDIA SimReady FAQ](https://docs.omniverse.nvidia.com/simready/latest/simready-faq.html)要求區分結構及 runtime 行為；[EmbodiedGen](https://github.com/HorizonRobotics/EmbodiedGen)是後續生成候選，不代表本機已接通。以本機 6.0.1 相符 API 為準，不升級共享環境。

此次只有資料盤點、引用與文件更新，沒有增加測試案例或重跑 GPU。證據：runs/20260918T005159Z_delivery_audit。
