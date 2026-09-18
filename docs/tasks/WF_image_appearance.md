# WF：圖片電鑽外觀修正
Status: done (topology/color data + physical/cold/export verified; human appearance pending)
用戶人工確認形狀尚可，但顏色怪、有多餘碎塊。只修圖片生成/authoring；不調紙箱鍵盤、physics驗收門檻或validator。
驗收：量測來源去背/components/顏色、保留raw與移除件；顯式largest政策而非所有資產自動刪小件；顯式PreviewSurface+linear vertex color；同例真生成/physics/cold/export；提供不重啟既有WebRTC的載入指令。人工顏色仍待確認。

全部量測/測試證據runs/20260918T063100Z_image_appearance_checks，報告reports/development/2026-09-18_image_appearance_fix.md。單一下一步：用户在既有WebRTC載入新版，比較顏色並確認移除件不是合法配件。
