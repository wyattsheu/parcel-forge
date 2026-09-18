# WebRTC 家目錄啟動入口
Status: done (script + preflight verified; livestream/human pending)
新增scripts/pf-webrtc，~/start_webrtc.sh相連；預設圖片電鑽export/完整UI/paused。VRAM與TCP/UDP ports檢查，不停止既有服務。
證據runs/20260918T062526Z_webrtc_start/result.json，--check exit0；--help exit0。實際stream startup與人工連線尚未測。
下一步：用户執行~/start_webrtc.sh，runtime.log出現[VIEW] READY後連線。
