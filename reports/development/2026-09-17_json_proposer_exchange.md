# JSON-only 模型提案交接：建置進度

完成固定 prompt 與模型回答檔案預檢；沒有模型 shell、檔案工具或自動 API 呼叫。
124 項離線測試、7 skipped，exit 0：runs/20260917T071800Z_proposer_exchange_tests。
基礎 smoke exit 0：runs/20260917T071612Z_s1_smoke。
實際 CLI 預檢 exit 0：runs/20260917T071817Z_proposer_exchange_cli/check.log。
該次回答是人工 offline fixture，不是模型成功證據，也未消耗 receipt 或啟動新物理。

小成功點：

| 功能 | 狀態 |
| --- | --- |
| 六份來源快照＋實測 gate | prepare 已執行並通過 |
| 固定 prompt／來源綁定／下一次 attempt | 已保存，attempt 2 尚未預留 |
| 回答原始 bytes＋prompt 雜湊 | check 已執行並通過 |
| 禁止改 probe、重複 JSON key、NaN、非 JSON、過大回答 | 測試通過 |
| prompt 篡改、symlink 輸入、三次 budget 耗盡 | 測試通過 |
| 真實模型呼叫 | not_tested，入口尚未設定 |
| 新物理／渲染／影片 | 本步驟未啟動 |

人工模型交接流程：

1. 開啟 [prompt.txt](../../runs/20260917T071730Z_s5d_proposer_prompt/prompt.txt)，將完整內容貼入你選擇的模型。不要附 API key。
2. 在本專案建立新的回答資料夾並保存完整原始回答，不要把原始回答修成可以通過的 fixture。另存提供者、model 名稱與時間；檔案式交接無法獨立證明模型身份或執行。

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
REPLY_DIR="runs/$(date -u +%Y%m%dT%H%M%SZ)_external_model_reply"
mkdir "$REPLY_DIR"
# 將模型原始回答存為 $REPLY_DIR/response.txt
./scripts/pf proposal-exchange check   --prompt-run 20260917T071730Z_s5d_proposer_prompt   --response "$REPLY_DIR/response.txt"
```

預檢成功只代表 ready_for_controller_submission，沒有候選物理成功判定。
把輸出 response run id 代入下一條，由正式控制器預留 attempt：

```bash
./scripts/pf repair-proposal   --source-run 20260917T000106Z_s2_open_box_sealed   --proposal runs/RESPONSE_RUN_ID/proposal.json
```

若期間別人已提交提案，prompt 中的 attempt 可能過期；正式控制器仍會拒絕。
prepare/check 不預留次數；正式提交後的拒絕仍會消耗 slot。不要反覆提交。
候選通過後，依 [中斷重跑規則](../../docs/REPAIR_RESTART_POLICY.md) 跑新的
pf box → repair-link-check → upstream-focused-check；原 profile 與 expected_outcome 保留。

自行重新建立 prompt（不呼叫模型、不消耗 attempt）：

```bash
./scripts/pf proposal-exchange prepare --source-run 20260917T000106Z_s2_open_box_sealed
```

來源標記：固定 JSON-only prompt、檔案式交接、重複 key 拒絕與大小限制是本專案設計。
不是 NVIDIA 通用 repair hook；NVIDIA 固定版本的 focused 驗收沿用既有接線（D045）。
控制器契約沿用本專案 v2（D044）。此模組不提供完整 actor sandbox。

本步驟不產生可看的模擬畫面。最近物理終態仍可用：

```bash
./scripts/pf view --run 20260917T064636Z_s2_open_box_sealed --scene scene_final.usda --ui --paused
```

使用者在加入 --paused 後回覆 OK；記為 user_reported_ok，不延伸為根因已修復或
所有 Play 路徑皆成功。串流占用時沿用既有 viewer，不停止別人的程序。

模型入口盤點與 blocked 記錄：runs/20260917T071817Z_proposer_exchange_cli/。
node/npm/ollama 未在 PATH 找到，沒有可呼叫的模型工具；API endpoint 未設定，未查看秘密。
這只限制本次真實呼叫，不代表機器不存在其他模型服務。整體仍約 70% 的粗略階段估計。
下一個動作：選定模型入口或拿到模型原始回答，保存 model/prompt/output，再做正式提交與新物理驗收。
