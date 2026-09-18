# 圖片電鑽：顏色與碎塊修正

用戶WebRTC人工回饋：形狀尚可，顏色怪，旁邊有小塊。此回饋是舊版的人工局部結果，不代表新版本外觀通過。Agent沒有做外觀判讀。

直接OBJ拓撲量測14070+232faces兩components。另trimesh.split預設repair會補面，報告14122不能當原檔面數，採直接索引14070為基準。去背alpha主區5281119pixels，另75000/10353pixels的小區塊：這是碎塊可能來源，不證明語意分割正確。

修生成器：显式component-policy keep/largest，default keep，largest只用於已回報此電鑽的修正；保留mesh_raw.obj及removed_components.obj，不放寬validator或collision。主體normalized長度從排除碎塊後bbox算，仍採.25m/1.5kg明示proxy假設。

修USD authoring：TripoSR圖片來源sRGB頂點色按標準transfer轉linear，明確UsdPrimvarReader_float3→UsdPreviewSurface diffuseColor binding；roughness .85/metallic0是視覺假設，不是真材料量測。照片中光影與模型預測仍烘進頂點色，不是校準albedo。頂點色解析度仍有限，不稱完整PBR或高保真texture。

方法來源：[TripoSR官方](https://github.com/VAST-AI-Research/TripoSR) 的mesh顏色輸出與單圖片重建；[OpenUSD PreviewSurface](https://openusd.org/release/spec_usdpreviewsurface.html) 的primvar reader/material graph。DSU component policy與本地證據交付為本專案實作，不稱NVIDIA已認證。

證據runs/20260918T063100Z_image_appearance_checks：11intake/5entry/2mesh-color tests exit0；generation/physics/cold/export總run20260918T062948Z_workflow exit0，出口exports/image_drill_appearance_v2。OBJ7065vertices/14070faces/1component；USD色彩序列readback最大誤差3.34e-8，shader graph在檔案中。這是serialized資料檢查，不是render。6紙箱鍵盤core hashes不變，未重跑它的physics。

WebRTC先保存並Stop，在Script Editor：
```python
import omni.usd
omni.usd.get_context().open_stage('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/exports/image_drill_appearance_v2/scene.usda')
```
Stage選/World/Drill按F，旋轉比較，再Play測外力移動。新版人工顏色/形狀/移除件review、render和material calibration均not_tested。既有viewer未停止。
