# 最新狀態 — 2026-09-18 圖片電鑽外觀修正

用戶舊版WebRTC回饋：形狀尚可，顏色異常/多餘碎塊。圖片路徑新增顯式largest connected-component policy（預設keep、保留raw/removed）；作者明示sRGB→linear頂點色與PreviewSurface material。
總run20260918T062948Z_workflow generation/physics/cold/export全exit0/pass→exports/image_drill_appearance_v2。7065vertices/14070faces/1component，移除232faces另存。color serialized readback誤差3.34e-8，roughness/metallic為假設，非校準PBR。11intake＋5entry＋2mesh/color tests pass。證據runs/20260918T063100Z_image_appearance_checks。
原紙箱鍵盤6core來源hash不變，未重跑其physics。既有viewer未停止；~/start_webrtc.sh預設新export，Script Editor可直接載入新版。新外觀人工/render/校準仍未測；不把physicspass升級外觀pass。雙入口/共用Skill/私人GitHub與跨機限制詳PORTABLE_SETUP。
單一下一步：用戶在既有WebRTC載入新版，確認顏色及移除小塊是否合理。
