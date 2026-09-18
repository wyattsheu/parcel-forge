# 雙入口與跨機交付建置進度

新增 `scripts/pf-workflow`（text intake / image dispatch）、`scripts/pf-machine`（installed interpreter metadata/API probe）、一份 Codex/Claude Code 共用 Skill，以及 `docs/PORTABLE_SETUP.md`。

NVIDIA 來源沿用 `docs/UPSTREAM_ADOPTION_PLAN.md` 所定 fixed-SHA 官方 Validation Agent / checkpoint / repair 分工；新增入口只是 dispatch，不替換官方 state 或重新設計 repair。跨機要求參考官方 requirements，實際以本機匹配 API 為準。Skill 路徑參考 OpenAI 和 Claude Code 官方文件，連結在 PORTABLE_SETUP。

## 本次驗證

證據 `runs/20260918T061200Z_portable_entry_checks/`：11 intake + 13 preflight + 5 runtime-override/stage-boundary tests 通過；Skill static validator 通過；API probe 找到本機 Isaac6.0.1 API files，未啟動 Kit。6 個品質核心來源 hash 相同，未調整紙箱/鍵盤物理。未為此重跑原紙箱物理，不把 hash 等同新物理驗證。

初次直接用未填參數的 drill template→needs_input，沒有呼叫模型。明示使用上一輪 proxy bundle 後，`runs/20260918T061026Z_workflow/` generation/physics/cold/export 全 pass；stage child-run 與 result hash 保存於 progress。產物 `exports/image_drill_portable_entry_v1/`。

文字紙箱鍵盤 bundle→unsupported / exit4，正確保留未支援取出/其他行為缺口；它不是原已測紙箱生成器失敗，也不表示原 viewer 品質改變。文字描述自動解析與 authoring 接 bundle 仍未完成，保留獨立 `pf-keyboard-package` 入口。

## 自行確認

```bash
./scripts/pf-machine
PYTHONPATH=src python3 -m unittest discover -s tests -p test_portable_entry.py
./scripts/pf-workflow --help
```

WebRTC：先保存/Stop；Script Editor 使用 delivery 文件的 PF_PROJECT_ROOT 指令載入 `image_drill_editor.py` 或 `keyboard_package_editor.py`。圖片 shape fidelity / 人工 / render / 材料校準、另一臺5090及两個 agent CLI invocation 均 not_tested。沒有新影片。

GitHub 私人 repo 交付結果另見 STATE/session；大型權重、venv、external 不上傳，新 runs 只提交此精簡證據摘要，歷史證據保留。

已確認GitHub PRIVATE；初次push commit4845ea0。fresh clone /tmp/parcel-forge-clone-1zadlbq6/repo 成功；若不設src import path unittest會失敗，依文件PYTHONPATH=src或等效sys.path設定後5/5通過，clone probe exit0，symlink共用內容相同。另5 NVIDIA adapter tests通過。未用clone重建模型環境或另機physics。
