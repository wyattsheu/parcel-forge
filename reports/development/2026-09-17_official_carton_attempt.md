# 官方自然語言紙箱生成：首次前置檢查

需求已凍結：runs/20260917T083229Z_official_carton_attempt/prompt.txt。
官方 geometry_agent_client.cli generate --help exit 0，證實文字入口存在。
未設定 Geometry service URL/API key、Build123d/delegated provider endpoint；
127.0.0.1:8776 未监听。僅查看配置是否存在，不輸出秘密。
結果 blocked：尚未呼叫模型、送出生成或產生 USD，不是生成失敗後回退本地箱子。

前一輪「官方可直接嘗試」少說了實際外部 authoring worker 前置條件。
Geometry service 是協調入口，本身不內建文字到 CAD 生成引擎。
僅安裝 client 或啟動空 service 並不能補足 provider。

已設定服務後可先查 provider 能力（將服務位址放環境變數，密鑰也只放本機環境）：

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
PYTHONPATH=external/usd-content-agents/apps/geometry_agent_service \
.venvs/usd-content-agents/bin/python -m geometry_agent_client.cli providers
```

確認 provider 支援 text、所需 export format 及語意零件後，使用官方 generate：

```bash
PYTHONPATH=external/usd-content-agents/apps/geometry_agent_service \
.venvs/usd-content-agents/bin/python -m geometry_agent_client.cli generate \
  --provider PROVIDER_ID \
  --prompt-file runs/20260917T083229Z_official_carton_attempt/prompt.txt \
  --format usda
```

這是設定完成後的指令範本，尚未執行。provider ID 不能自行虛構，且 geometry 輸出
不代表 Joint/Physics 及回彈完成；後續需獨立 authoring 與推開/放手驗收。

來源：external/usd-content-agents/agentic/.agents/skills/content-workflow-geometry/SKILL.md，
以及 apps/geometry_agent_service/README.md、geometry_agent_client/cli.py。
技能要求「Select providers explicitly」與「Query provider capabilities before authoring」。
具體阻擋是沒有服務/生成器設定，而非等待批准既有配置。

下一個動作：取得可用 Geometry service URL 與已註冊 provider ID；若沒有，先選定並
配置真正具備文字 authoring 的 backend，再重跑 providers/generate。
本次未執行物理 smoke，未聲稱歷史物理結果已重新驗證；未動 viewer、runtime、driver 或服務。
