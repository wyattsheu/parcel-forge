# 圖片電鑽工作流建置成果 — 2026-09-18

本卡完成單圖→真實神經網格→USD→落地/外力移動→新目錄/新程序冷載入→可攜交付。這是剛體幾何基線，沒有宣稱完整通用工作流/精確電鑽重建/真實材料校準。

## 建置與來源

後端：TripoSR，官方 https://github.com/VAST-AI-Research/TripoSR ，MIT source/model；固定 source107cefdc244c39106fa830359024f6a2f1c78871，model5b521936b01fbe1890f6f9baed0254ab6351c04a。
選擇理由：可無API key本機執行、直接OBJ/GLB、可不錄影片，先建立實跑基線。EmbodiedGen仍是後续URDF/推估物性候選，沒有宣稱已安裝。
獨立 .venvs/triposr：torch2.8/cu128；沒有改Isaac runtime/driver/toolkit。CUDA12.8與Python標頭使用已有安裝唯讀引用。
網格擷取 torchmcubes 初次失敗缺Python.h、次次失敗C++20/lerp；在獨立副本用C++17修正，patch config/patches/torchmcubes_torch28_cpp17.patch，原upstream保留。元件MPL2.0與TripoSR MIT分開；venv freeze/命令/失敗都保存。
輸入照片作者 Matti Blume（MB-one）、CC BY-SA4.0；原圖3888×5184。曾取得97×102的公共領域圖，未用它推論。來源與所有轉換已收入 exports/image_drill_v1/LICENSE_SOURCES.md。
本次把最大bbox尺寸指定0.25m、mass1.5kg，全部assumed。圖片本身沒有提供可靠尺度或質量，不能冒稱實測。

## 本次新增實作

- pf-image-task 增加TRIPOSR後端與RGB頂點OBJ支持；強制task/bundle預檢。
- pf-image-generate：真正單次模型執行，重查preflight/provider pin/modelhash/inputhash/GPU，保存版本、輸入、耗時、峰值VRAM、原始mesh；不錄影片。
- pf-image-usd：mesh嵌入asset.usda，頂點顏色；獨立guide collider，PhysX convexDecomposition；free dynamic、CCD、240Hz/CPU/TGS、mass/inertia讀回、落地、穩定與推力測試。scene在設定後匯出，相對引用asset。
- pf-image-cold：複製到新run，以新Isaac程序重跑落地與受力；驗交付不用先前stage內存。
- pf-image-export：冷載入通過才打包、檢查hash、不覆蓋既有名字；輸出來源、manifest、驗證、loader。
- image_drill_editor.py：只選冷載入成功run，於現有viewer開scene；原生滑鼠力，不寫pose/animation。

## 實測結果與證據

| 項目 | 結果 | 證據 |
|---|---|---|
| intake | prepared | runs/20260918T011657Z_image_intake |
| 模型執行 | exit0、generation pass；7183vertices/14302faces | runs/20260918T012226Z_image_generation |
| 推論/mesh/總時間 | 2.718s / .185s / 76.899s（host含起動）；首次總時間含去背/cache | 同上；provider total74.031s |
| VRAM | peak PyTorch allocated2033397248 bytes，非整台/GPU全部使用量 | provider_result.json |
| OBJ交接 | checked；不因交接而升級生成/物理 | runs/20260918T012711Z_image_artifact_handoff |
| USD物理/狀態讀回/headless | pass，10checks；mass1.5kg，15N/.2s位移.116632m | runs/20260918T012639Z_image_drill_usd |
| 新目錄新程序cold physics/readback | pass，5checks，位移.116632m | runs/20260918T012704Z_image_drill_cold |
| 可攜export | exported/hash match | exports/image_drill_v1；runs/20260918T012820Z_image_export |
| offline render/影片 | not_tested / not_requested | 不當成物理失敗也不當成成功 |
| WebRTC人工觀看/形狀保真/校準/接觸保真 | not_tested | 等人工/實物量測 |

USD前兩次失敗保留：012358Z質量張量scalar型別；012442Z NumPy bool不可JSON序列化。第二次Kit外部exit0但沒有result，host判fail；證明不能只信退出碼。改資料轉換/序列化，未改測試容許值。
碰撞cook保留近似，不宣稱握把空隙/扳機凹槽已驗。截圖非黑仍不足以證明這些形狀；這次未新增render以避免額外開銷。

## 在現有WebRTC看3D、操作

先儲存現在工作並按Stop。於Script Editor執行：

```python
from pathlib import Path
p = Path('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/scripts/image_drill_editor.py')
exec(compile(p.read_text(), str(p), 'exec'), globals())
```

載入後選中/World/Drill，按F定位。Timeline停止時旋轉視角看握把、夾頭、電池、背面；請與原照片比較，不能由agent代替此人工判斷。按Play後讓它落地，Shift+左鍵拖動施力，可拉起再放手。這是剛體，不會捏凹或轉動扳機。
概念：施力互動不同於改pose。單一實驗：保持其他設定，將 /physics/pickingForce 從50改25，比較拖動反應；此參數是viewer施力尺度，不是模型材料。

```python
import carb
carb.settings.get_settings().set_float('/physics/pickingForce', 25.0)
```

如只需開場景：Stop後 `omni.usd.get_context().open_stage('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/exports/image_drill_v1/scene.usda')`。其原生滑鼠設定仍以現有app為準，推薦用上述loader。

## 重新執行（會建立新run）

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf-image-generate --run runs/20260918T011657Z_image_intake
```

讀回傳generation run後，依序：

```bash
./scripts/pf-image-usd --run runs/NEW_GENERATION_RUN
./scripts/pf-image-cold --run runs/NEW_USD_RUN
./scripts/pf-image-export --run runs/NEW_COLD_RUN --name NEW_EXPORT_NAME
```

NEW_*是前一步印出的實際目錄名，不能照字面執行。使用另一張圖片時先用prepare、填可靠尺度質量或明確假設來源；不跳過預檢。

下一步：人工WebRTC確認電鑽形狀；若握把空隙/夾頭/電池失真，修生成路徑再用同例重跑，不放寬驗收。下一輪才比較TRELLIS/其他後端，不並跑多物件。
