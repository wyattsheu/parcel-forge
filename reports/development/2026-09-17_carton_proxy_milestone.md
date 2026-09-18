# 紙箱工作流建置進度：四蓋折痕代理模型

本階段已建立可重現的四蓋 USD／PhysX 代理模型，獨立開啟順序、低／高載荷與循環診斷均通過。
**完整使用者需求尚未全部完成**：板面 MD/CD 正交異向性彎曲、實物校準、Isaac Lab整合、機器人接觸拆箱未驗證。
不是實際瓦楞層有限元素模型，也不是官方 Codex SDK child／Geometry provider 的鍵盤流程復現。

## 建置的每個小成果

| 階段 | 建置到哪裡 | 可自行確認的證據 |
| --- | --- | --- |
| 1 四蓋幾何 | 固定箱體＋4片上蓋＋4 revolute joints，9個碰撞板件 | `20260917T114330Z_ext1_carton/asset.usda`、官方檢查 |
| 2 本機物理API | Isaac6 CPU PhysX，240Hz，質量／慣量／增益tensor讀回 | `carton_result.json` 的 runtime、mass/inertia/drive_readback |
| 3 折痕內部狀態 | k=.04、c=.003、Y=.03、η=.08，Backward Euler黏塑性更新 | crease_model.py；離線133 tests、7 skipped，exit0 |
| 4 摩擦單位 | `PhysxJointAxisAPI:angular` 靜／動摩擦力矩 .005 N·m，讀回吻合 | `20260917T114240Z_ext1_carton/friction_readback`；legacy coefficient變0避免混用 |
| 5 低／高載荷 | 主蓋保持打開；一片次蓋低載荷回彈、另一片高載荷留角 | `20260917T114240Z_ext1_carton`，coupon_diagnostic_status=pass |
| 6 開蓋順序 | 主蓋0–3秒、次蓋3–6秒，6秒後全部外加驅動載荷撤除 | `20260917T114330Z_ext1_carton`，opening_diagnostic_status=pass |
| 7 循環軟化 | 4次開、3次反向關；模型降伏力矩下降且有下限 | `20260917T114414Z_ext1_carton`，cyclic_diagnostic_status=pass |
| 8 可播放紀錄 | 每秒30組四蓋tensor位置／姿態，USD重讀誤差0 | 每案 recording.usda、link_poses.csv、recording_validation.json |
| 9 執行途中回報 | 生成、readback、每3秒模擬進度、完成判定 | progress.jsonl；這是**執行進度**，不同於本建置報告 |
| 10 NVIDIA規則 | 41規則、根defaultPrim修正、官方／自訂負例 | `20260917T114413Z_ext1_usd_check/usd_check.json` |

碰撞與self-collision始終啟用；沒有鬆綁驗收或把舊fail改pass。
原混合載荷案例仍因關閉主蓋擋住次蓋而失敗：`20260917T113726Z_ext1_carton`。
新診斷分別回答材料狀態／互撞順序，不能反過來宣稱原案例通過。
`carton_result.json.status`與CLI exit1保留原 mixed gate；新情境看對應 diagnostic_status。
一般Kit raw exit0不代表驗收通過。recheck 的 pass只表示重算判定一致。

## 自行執行的指令

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
# 重新生成、真實物理執行，每次新run，約20秒模擬時間
./scripts/pf-carton --physics-device cpu --scenario opening-order --crease-friction-nm 0.005
# 對照低／高力矩，只讓被測次蓋放手（主蓋持續保持打開）
./scripts/pf-carton --physics-device cpu --scenario crease-coupon --crease-friction-nm 0.005
# 四次開啟、三次關閉，30秒模擬時間
./scripts/pf-carton --physics-device cpu --scenario crease-cyclic --crease-friction-nm 0.005
# 既有證據的USD檢查（不啟動Kit、不使用GPU、不重新模擬）
./scripts/pf-carton-usd-check --run 20260917T114330Z_ext1_carton
# 既有證據重新計算判定（不重新模擬；fail仍保留）
./scripts/pf-carton-recheck --run 20260917T114330Z_ext1_carton
# 實測角度／塑性參考角SVG與簡短回報，輸出新的review資料夾
./scripts/pf-carton-report --run 20260917T114330Z_ext1_carton
```

三個物理診斷命令仍exit1（保留mixed gate），請確認各自的 diagnostic_status=pass。
USD檢查、重算一致性、產生報告三個命令成功時exit0。先看GPU inventory，資源不足會blocked，不能關掉他人程序。
終端機先印出新run與progress.jsonl；可在另一個終端用`tail -f <新run>/progress.jsonl`看執行步驟。

## 在既有WebRTC看實際開蓋動作

先儲存目前工作、停止timeline，再於 **Script Editor** 貼上並執行：

```python
import omni.usd
omni.usd.get_context().open_stage("/mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260917T114330Z_ext1_carton/recording.usda")
```

選 `/World/Carton`、按F定位；timeline回到起點，按Play。
前3秒主蓋開、3–6秒次蓋開、6秒後放手回復。這是實測軌跡回放，只有recording關閉物理／移除關節，原asset碰撞與物理不變。
不是即時Python塑性控制器；直接播放asset.usda不會自行執行塑性／疲勞更新。
人類WebRTC觀看尚未確認；本agent未聲稱看過圖片／影片。

要看單折痕，改成 `20260917T114240Z_ext1_carton/recording.usda`；看重複開關，改成 `20260917T114414Z_ext1_carton/recording.usda`。
看初始幾何改asset.usda、看終態改scene_final.usda，兩者都保持timeline停止。
各案SVG：使用上述pf-carton-report指令生成，圖表来自CSV，不是相機render。
本階段未自動產生MP4，避免重複GPU渲染；可直接點recording.usda並在編輯器播放。

## 方法來源標記

- **[使用者需求]** [原始prompt](../../contracts/carton_codex_prompt.md)：RSC四上蓋、彈／塑性、遲滯／軟化及估計參數。數值不是文獻校準。
- **[本機工程手冊]** [Handbook §17](../../IsaacSim_Asset_Workflow_Handbook.md)：固定箱體、剛體蓋、revolute joint、先測單片再互撞。早期混合案例沒有分離主次蓋，現以獨立診斷補齊。
- **[NVIDIA／OpenUSD]** [DriveAPI](https://openusd.org/dev/api/class_usd_physics_drive_a_p_i.html)：USD角度drive以degree，程式SI/radian增益轉換。
- **[NVIDIA]** [PhysxJointAPI](https://docs.omniverse.nvidia.com/kit/docs/omni_usd_schema_physics/latest/physxschema/class_physx_schema_physx_joint_a_p_i.html)：legacy jointFriction是無因次係數，不能標成N·m。
- **[版本匹配本機API]** `isaacsim.core.experimental.prims.impl.articulation.py` 的 get/set_dof_friction_properties、get_dof_positions、get_dof_gains；Isaac6 PhysxJointAxisAPI angular friction effort補上N·m阻力。
- **[本專案方法]** 黏塑性Backward Euler、accumulated-plastic softening、力矩等效drive offset、開啟順序、事件式目標寫入、獨立診斷profile與30Hz tensor姿態回放；不是NVIDIA內建紙箱模型或完整paper複製。
- **[研究參考]** [Beex & Peerlings 2009](https://publications.uni.lu/bitstream/10993/17431/1/BeexPeerlings2009.pdf) 可作紙板壓痕研究參考；不能直接拿非本瓦楞樣品的數值校準本箱。見 [材料研究](../../docs/research/CARDBOARD_MECHANICS.md)。

NVIDIA通用USD規則不等於physics準確度標準、SimReady認證、機器人拆箱成功或真實紙板驗證。
根defaultPrim第一次被官方抓到fail，修正生成器後pass；負例重新設定到child確實fail。
自訂missing-hinge／collision-disabled負例也確實fail，但不能說這些由通用官方規則保證。

## 已量測的數值敏感度與待辦

早期legacy摩擦係數.01版本，240／480Hz單折痕診斷皆pass；高載荷次蓋終態角差 .023290945°、塑性參考角差 .013974462°。
證據 `20260917T113540Z_ext1_dt_comparison/comparison.json`。這只是一組兩步長敏感度對照，不是完整收斂階數證明；也不是新N·m摩擦設定的收斂證明。
四循環純函式資料 `20260917T113028Z_ext1_crease_checks` 的strict每循環下降檢查fail，因第3／4循環都到.015Nm下限，保留此結果；它不能用來拒絕設有下限的軟化模型。
兩循環strict診斷pass；完整四循環有下限的行為另外由133項離線測試驗證。兩種判定不混為一談。

下一階段先取得實物force/angle/lever-arm資料，依 [校準實驗與空白模板](../../docs/research/CARTON_CALIBRATION_PROTOCOL.md) 辨識，再用保留測試集驗證。
板面MD/CD彎曲、含實體瓦楞層、破裂／撕膠帶、真實robot contact與IsaacLab runtime integration仍未完成。
所有參數uncalibrated_assumption；目前殘餘角可能受接觸／摩擦／限位／sleep影響，速度為零不等於已量到力矩平衡。

最終程式／syntax／133 tests重驗：`20260917T114752Z_ext1_release_checks`，unittest exit 0；git diff --check exit 0。
