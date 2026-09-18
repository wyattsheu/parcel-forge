# A/B/C 整合執行：修復與背景程序離線驗證

三份交接均已審閱，保留原始 handoffs 不覆寫。B 的契約衝突已修正，C 的腳本已核對並補測，A 的上游接線限制已納入後續計畫。主線未 commit/push。

已實作與驗證：

- **修復 v2**：唯一有效格式為 repair_proposal/2，來源 run/spec SHA256/attempt 全部必填，僅一筆 /geometry/fault → none。舊 v1 schema 拒絕所有文件，舊內容保留在 runs/20260917T025429Z_bc_integration/repair_proposal_v1.schema.json.before 與 D044。
- **來源與次數**：CLI 使用 --source-run，凍結六個證據檔並重新檢查。控制器以 flock 和 append-only receipt 序列限制每個原始來源最多三次；拒絕提案也消耗已預留的次數。第四次與重送 attempt=1 都會拒絕，測試在隔離 fixture 執行。v1 歷史提案不回填 v2 的強制預算。
- **路徑**：只讀本地來源 run 與 contracts/repair_proposals、runs 下提案，拒絕 symlink 與路徑越界。這是受信任工具輸入限制，沒有宣稱完整 actor sandbox。
- **證據鏈**：repair-link-check 核對來源快照、proposal、candidate、驗證 request 的 byte hashes、允許修復重新計算、原始 profile 不變及 receipt。已核對既有修復後物理內容；沒有重新模擬，也不以內容匹配宣稱新的時間順序或模型修復成功。
- **背景工具**：C 新增 exception result、--status、重複啟動 exit 3、工作目錄碰撞後綴。主線另修正後綴工作漏掃、零 exit 卻無有效證據仍失敗、壞 request 的已完成失敗結果優先顯示，以及啟動 flock 防止兩個啟動程序同時通過重複檢查。保留 exit 3 拒絕政策，不默默重用或排隊。

[統整證據](../../runs/20260917T053507Z_abc_integration_completion/suite.json)。121 項測試、7 項跳過，exit 0；JSON Schema 與 guard 正例／反例一致，exit 0。背景程序測試是隔離 fake pf，檔案寫明 FAKE-NOT-A-REAL-VIDEO，沒有新 GPU 渲染。曾經完成的真實背景工作僅查 --status，exit 0；不把 fake pass 報成 renderer pass。

自行確認，不花影片渲染時間：

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
PYTHONPATH=src python3 -m unittest tests.test_repair_guard tests.test_background_video -v
./scripts/pf-video-background --status 20260917T015837Z_background_video
./scripts/pf repair-link-check --proposal-run 20260917T025702Z_s5d_repair_proposal --validation-run 20260917T015711Z_s2_open_box_no_bottom
```

預期三條 exit 0；第二條 state=completed，第三條 hash_chain_verified 並明列是既有內容鏈接。

新的提案介面：

```bash
./scripts/pf repair-proposal --source-run <原始run-id> --proposal <v2提案檔>
```

不要無限重跑 fixture：已提交的 v2 restore_bottom fixture attempt=1 不能再用同一來源預算假裝第一次。後續提案必須填實際下一次 attempt；三次後需要停止，而不是新建來源 run 來洗掉預算。現有舊報告的 --case 範例是歷史介面，改看 docs/REPAIR_CONTRACT.md。

A 的來源審查確認 pinned upstream 的 ValidationTemplateRegistry 拒絕第五個模板；USD topology/physics 修復不是本地 JSON spec 修復。先前「官方 coding-agent 直接修箱 spec」的描述收斂為外部 actor 提案＋本地 gate＋官方驗證/checkpoint，不杜撰一個不存在的 plug-in。policy/metadata 可以承載中繼資料，但不會執行新自訂 checks。Node/npm 缺失不阻擋目前 deterministic physics_sane 流程；有需要的 child-runner 路徑才處理。

仍未完成：完整 actor 權限隔離、真實模型產生提案、新的 repair physics 執行鏈、官方中斷恢復實驗。Landlock 的 content-write 探測與官方 checkpoint 讀回只是此前已量測的部分能力。A 的 asset-validator blocked/error 轉換建議也尚未接線。

本輪必要 smoke physics-only：runs/20260917T025342Z_s1_smoke，exit 0、physics/readback pass，render not_tested。WebRTC 人工確認 not_tested，沒有新影片或新画面。

下一個動作：以官方 focused validation 的分階段操作設計與執行受控的中斷／恢復實驗，不呼叫模型、不停止共享程序。
