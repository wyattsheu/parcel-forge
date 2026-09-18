# WF-P0：通用契約、能力圖與歷史需求對照

Status: done (verified offline) — 契約設計與範例一致性；不是材料／生成器驗證。
Parent: [泛用工作流主計畫](../plans/2026-09-18_general_asset_workflow_master_plan.md)。
Mapping: S6 需求語義之前置設計，接 EXT2／S5／S7；不重設既有里程碑。

## 目標

讓不同物件都能用同一組部件、接合、行為與任務結構描述；能顯式說出目前不支援什麼。完成本卡不代表生成器或物理已實作。

## 開始前

讀 STATE、ROADMAP、ENVIRONMENT、主計畫及最新 session；保存 git status，保留所有既有變動。
資源允許時執行 ./scripts/pf smoke 保存新基線；資源不足寫 blocked，不宣稱物理通過，仍可進行離線規格工作。
先盤點 contracts、profiles、repair guard 與 registry 相關程式，避免同名 schema 有兩套含義。

## 本卡工作

1. 確定 task_brief、assembly_graph、parameter_cards、asset_contract、capability_report、validation_plan 的欄位、版本與引用規則；先寫文件與 fixtures，不新增服務。
2. 將剛體、被動關節、摺痕、板／膜彎曲、壓縮與剝離寫成能力條目，標 implementation／evidence／unsupported，不因列入字彙就算支援。
3. 用紙箱、可拆包杯、不規則剛體及未知機制各寫一個示例。需求可缺值，但缺值原因和阻擋条件需可表達。
4. 將前期計畫歷史問題逐一映射 requirement ID、check ID 或 capability gap，保留來源。
5. 給 EmbodiedGen 單物件路徑寫 qualification 規格：版本、輸入／輸出、尺度、環境隔離、權重／授權、資源及冷載入測試；本卡不安裝。
6. 明訂 next-stage 可用與 needs_input／unsupported／conflict 規則，確認舊 case schema 不被靜默重新解讀。

## 完成條件

- 同一契約可表達四種示例，不需每物件新增一份 schema。
- 可拆包杯不能把封閉殼列為等價替代；剛板不能宣稱 MD/CD 變形已支援。
- source／unit／confidence／測試缺口／runtime requirement 均能追蹤。
- 每項歷史重大問題有對應防線；未實作 check 清楚標 planned。
- qualification 規格可讓另一位執行者接手，不靠閱讀整段對話。
- 保存本卡檢查輸出、建置報告、狀態與 session；沒有啟動 P1 或外部模型。

## 刻意排除

材料校準、MD/CD 實作、撕裂／膠帶模型、registry 重構、安裝 EmbodiedGen、付費 API、生成影片及訓練。

## 教學與實驗

概念：物件種類與任務／能力分開。
離線實驗：同一包覆幾何只把任務從搬運改成解包，應新增接合可釋放與可分離測試需求；如果仍判相同能力充分，契約設計失敗。
本卡沒有新的 3D 模型；WebRTC 不適用，不能用舊畫面當作契約已生效的證据。

## 下一步

開始第 1 項契約盤點與字段設計。完成本卡後才建立／執行 P1。

## 本次交付

契約：docs/WORKFLOW_CONTRACT.md；四種範例及能力：contracts/workflow/；歷史防線 history_requirements.json；provider 資格卡：docs/research/EMBODIEDGEN_QUALIFICATION.md。
離線一致性與引用检查 exit 0，證據 runs/20260917T165040Z_wf_p0。全部新增 physical checks 仍 planned。
