# 最新狀態 — 2026-09-18 雙入口與可攜交付

pf-workflow文字intake/圖片dispatch、installed-Isaac本機設定覆寫/API probe、Codex與Claude Code共用薄Skill已實作。11 intake＋13 preflight＋5 boundary＋5 NVIDIA adapter tests和Skill靜態驗證pass。圖片完整入口實跑runs/20260918T061026Z_workflow generation/physics/cold/export pass→exports/image_drill_portable_entry_v1。明示.25m/1.5kg proxy假設，非校準。
紙箱＋鍵盤6個核心來源hash保持原狀，這次未重跑原案例physics。文字bundle目前仍會列出unsupported能力缺口，不宣稱通用文字生成完成。NVIDIA既有fixed-SHA integration保留；新圖片route nvidia_validation not_tested。
另一臺5090/其他Isaac版本、兩個AI的實際Skill invocation、render/影片、人工作證/外形保真/校準未測。部署入口docs/PORTABLE_SETUP.md；本次報告reports/development/2026-09-18_portable_entry.md。已推送私人GitHub https://github.com/wyattsheu/parcel-forge；全新clone的Skill連結/API probe/5 boundary tests pass（同一臺來源機，不是5090）。
單一下一步：在5090 clone，依docs/PORTABLE_SETUP.md綁定現有Isaac interpreter並跑pf-machine，再執行同一紙箱鍵盤案例。
