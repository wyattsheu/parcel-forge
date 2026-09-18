# 單一代表性驗收：紙箱裝鍵盤

使用者要求只驗一個主要案例；新鍵盤包裹已生成並在 PhysX 實測。此前四蓋回歸為既有測試，不擴展其他新模型。

## 結果與範圍

命令 `./scripts/pf-keyboard-package` → exit 0。
證據：runs/20260917T235608Z_keyboard_package/result.json、runtime.log、launch.json、asset.usda、scene_final.usda。
四片蓋由外力依序打開，放手後大蓋 268.32°、小蓋 269.10°；鍵盤留在箱內，質量讀回 0.64999998 kg。
鍵盤是有 90 個視覺鍵帽的剛性內容物代理，碰撞是底座；不能按鍵。尺寸和質量是假設，不是照片辨識或官方鍵盤生成展示。
箱底固定是開蓋量測夾具，不代表自由箱體／機器人工作流已驗收。取出、接觸事件、逐步穿透深度、渲染及人類 WebRTC 本次 not_tested。
四個機器 checks 通過只代表本範圍，不是完整物理包裹 pass。

第一次 runs/20260917T235543Z_keyboard_package 因 board_mass import 錯誤失敗；修正來源後重跑。失敗證據保留。
既有四蓋回歸 runs/20260917T235408Z_ext1_carton_pull exit 0；亦非鍵盤取出測試。

## 自行執行同一測試

在專案根目錄：
```bash
./scripts/pf-keyboard-package
```
這會另建新 run、無 livestream，不重啟你的 viewer；不用另外跑其他案例。

## 在既有 WebRTC 載入

先儲存目前工作、停止 timeline。在 Isaac Script Editor 執行：
```python
from pathlib import Path
_p = Path("/mnt/HDD4/wyattsheu/ITRI/parcel-forge/scripts/keyboard_package_editor.py")
exec(compile(_p.read_text(), str(_p), "exec"), globals())
```
這是新 loader，語法檢查通過，尚未在使用者 GUI 驗證；它載入最新機器通過 run 的初態 asset.usda，並接摺痕 callback。不是 final 動畫。
按 Play，選 /World/Carton 按 F 定位；依 viewer 原生 physics drag（既有版本為 Shift＋左鍵拖曳），抓大蓋外緣拉，再放手。不要用 transform gizmo 移動蓋子。
大蓋先開，再拉下方小蓋；小蓋被關閉的大蓋擋住是正常碰撞，不能把蓋子互穿當成獨立操作。
只改拉動幅度，比較小幅彈回與較大折彎後留摺。材質參數未真實校準；這裡固定箱底，整箱不能拖走。
畫面若沒有反應，保存 loader 輸出與目前 viewer 狀態；不要用開／關按鈕取代受力操作。

## 本次預檢改進

新增 carton_keyboard 的複合部件／containment／取出需求，補 scalar、finite、units、positive、來源卡與 payload 長寬适配檢查。
預檢仍 exit 3：payload_extraction 無驗收證據，這項 registry 故意不改成 implemented；場景能打開不等於取出已完成。

來源：自訂參數化 keyboard_package.py；紙箱沿用 carton_author／crease_model／carton_force_probe，技術理由見 D061、D068。没有直接使用圖片生成器。
下一步：同一鍵盤包裹的接觸／取出與自由箱體觀測，保持單一案例。
