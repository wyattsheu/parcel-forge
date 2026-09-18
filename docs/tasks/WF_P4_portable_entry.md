# WF-P4：雙入口、薄 Skill 與可攜交付

Status: done (bounded entry / local portability / private push; other-machine pending)
有界範圍：統一文字規格 intake 與圖片已支援 pipeline；本機環境覆寫、read-only API probe、clone 操作文件與私人 GitHub 交付。
不新增模型服務，不宣稱通用文字到任何物理資產已完成，不修改共享 Isaac 或 driver。
驗收：最小 intake benchmark、覆寫測試、probe、失敗停止、Skill validation、Git 大檔/secret pattern 檢查與推送結果。跨機相容需另機實跑，不以版本字串冒充驗證。

驗證：34 relevant offline tests、Skill static、API metadata、本機fresh clone、完整image dispatch generation/physics/cold/export。證據runs/20260918T061200Z_portable_entry_checks；私人GitHub wyattsheu/parcel-forge。
文字入口只intake，通用文字authoring / bundle接原鍵盤生成器仍未完成；兩個AI實際invocation與另一臺5090未測。不擴充本卡。
