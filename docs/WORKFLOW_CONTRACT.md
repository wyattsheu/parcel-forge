# 工作流契約 v1（P0 設計與離線範例）

新格式 `parcel_forge.workflow_bundle/1` 不重用 `case/1` 或 `repair_proposal/2`；現有案例與 repair guard 不被修改。
六段資料：task_brief、assembly_graph、parameter_cards、asset_contract、capability_report、validation_plan。
範例位於 contracts/workflow/examples；只是需求描述，不是新生成物件。P0 的 checks 都是 planned，不能推論物理通過。

| 段落 | 必要欄位與含義 |
| --- | --- |
| task_brief | intended_task、initial_state、base_mode、success_observations、required_behaviors |
| assembly_graph | parts（唯一 ID／frame／material）、interfaces（唯一 ID／a／b／kind；兩端必存在） |
| parameter_cards | id、value、unit、required、provenance、source、confidence、conditions、derivation；未知值為 null |
| asset_contract | passive、forbidden_simplifications、runtime_requirements、approximation_scope |
| capability_report | status 與下一階段的逐項模型／證據／能力缺口；P0 為 not_evaluated |
| validation_plan | required_checks、check_status；必測項須包含任務及能力需求，未知項不得忽略 |

優先判定規格衝突／結構錯誤，其次 unsupported capability，其次 needs_input，最後 ready_for_planning。ready_for_planning 不等於 ready_for_generation，更不是 pass。
初態 unconfirmed 或必要參數 null 時 needs_input；使用者不在時可整理來源與提案，但不能把提案當確認。
planned check 在下游生成前仍須連接真正 validator；有能力 metadata 不代表已有實作。
來源 provenance：user_given、measured、manufacturer、literature_matched、literature_analogy、derived、assumed、unknown。
後續機器驗證須拒絕未知欄位與版本，驗證 finite／units／引用／runtime／禁用簡化；不能只檢查 JSON 可解析。

通用性實驗：複製同一組 mug/wrap/tape 部件，只將 intended_task 從 move 改成 unwrap，測試需求必須增加膜變形與接合釋放；原封閉外殼不可視為任務等價。
來源：主計畫、既有 D060–D068、兩份使用者開發附件。能力清單的 historical_evidence 不是本次重測證據。

## 可移動性 gate（2026-09-18 修正）

機器人搬運／取出包裹預設 base_mode=free。move、open_and_extract、open_unwrap_and_extract 禁止 fixed；自由物件必含 structure.mobility，漏項預檢 conflict。
生成後 structure.mobility 必須驗 dynamic rigid body、無世界／靜態錨定路徑，以及已保存的外力位移；僅刪 FixedJoint 不足以通過。
本次 keyboard fixture 驗世界 joint 端點及已知箱體剛體，另以推力驗位移；任意新資產還需檢查間接静態／關節鏈約束，不能宣稱已有通用 USD 錨定分析器。
固定試片只允許獨立 lab task，不當成可交付 robot prop。地面摩擦不等於黏死，不應為容易拖動而關碰撞／重力或設零摩擦。
