# WF-P3A-1：圖片任務入口與產物交接

Status: done (verified offline)
授權：使用者要求繼續實作圖片生成並研究 Marso。父計畫 P3a；本卡只做圖片資格入口，不擴張其他物件或服務。

範圍：手持電鑽單例；強制既有 workflow preflight、保存不可變圖片/需求/來源/hash、固定候選後端版本、接收並檢查外部 mesh 產物。來源授權為使用者陳述，程式不冒稱已審查通過。幾何產物交接不等於生成/物理/人工驗證。

驗收：有效準備輸出可重現 request；缺資料/不支援能力/壞圖拒絕；產物隔離保存，無檔/壞 mesh 拒絕；離線測試輸出保存 runs/。不改 Isaac/driver、不新增服務、不填外部公司表單。

未含：後端套件安裝、權重下載、真實模型生成、USD 轉換及 WebRTC。下一張卡才驗本機後端及生成。

證據：runs/20260918T010828Z_image_intake_final_checks（10/10）与 runs/20260918T010602Z_image_intake_checks（13 preflight tests）。詳細報告 reports/development/2026-09-18_image_intake_marso.md。模型/物理/render/WebRTC 均 not_tested。

補充：阻擋來源資料夾包含輸出run造成遞迴複製；最後11圖片測試 exit0，證據 runs/20260918T010854Z_image_intake_overlap_checks。
