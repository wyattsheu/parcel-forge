> 2026-09-17 評估更新：以下為早期方案，非材料驗收結果。折痕不一定有固定屈服峰；
> 需量測載入／卸載／循環 M–angle 曲線。四點彎曲不能單獨校正折痕；deformable
> 能力限制尚未依本機版本驗證。最新順序與測試規格見
> reports/development/2026-09-17_flaps_keyboard_assessment.md。

# Task EXT1: RSC flaps and crease mechanics
Status: in_progress (user-authorized Codex four-flap prototype, not part of S0-S7)
Depends on: S4 verified, and D017 (dt-dependent containment) resolved

Background and sources: `docs/research/CARDBOARD_MECHANICS.md`.
Handbook section 17 places flaps, cups and packaging materials after the rigid
baseline. This card exists so the requirement is recorded, not so it jumps the queue.

## Goal
The box becomes a Regular Slotted Container with four flaps that fold at crease
lines, resist until a threshold, and stay folded once creased.

## Stage A - geometry only (pure maths, no physics)
Extend `geometry.py` with the RSC flap table. The defining rule is exact and
testable offline:

- all four flaps have the same length
- `flap_length = W / 2`, so the two outer flaps meet at the centre line
- flaps exist at both the top and the bottom opening
- reject specs where a flap would be longer than the face it folds against

Acceptance: unit tests pin `flap_length == W/2` and that the two outer flaps meet
with zero gap at the centre for the demo box (W = 0.20 -> each flap 0.10 m).
No simulator involved, same as `tests/test_geometry.py` today.

## Stage B - flaps as articulated rigid bodies
Each flap becomes a child rigid body joined to its wall by a **revolute joint** on
the crease line. Exactly one articulation root; flaps are links, never free bodies.

- joint limits: the physical fold range (roughly 0 to 180 degrees)
- joint drive: stiffness and damping give the restoring torque -- the resistance
  before the board gives
- all values start as `uncalibrated_assumption` in provenance

Acceptance: flaps hold their pose under gravity; a commanded fold reaches the
target; nothing separates from the articulation root; the existing S2 containment
cases still pass unchanged with flaps open.

## Stage C - the crease yield rule
PhysX joints are elastic, so permanent creasing must be explicit:

1. monitor joint torque
2. when it exceeds `crease_yield_torque_nm`, move the drive rest angle toward the
   current angle and reduce drive stiffness by `crease_softening_factor`
3. record every yield event in the run evidence with the torque that caused it

This encodes the documented fact that a crease is permanently weaker than the
surrounding board, and that folds are the most common box failure site.

Acceptance: a flap pushed below the threshold springs back; pushed above it, it
stays folded and is measurably easier to fold the second time. Both directions are
separate test cases -- a model that only ever yields is as wrong as one that never does.

## Explicitly out of scope
- Deformable/FEM board. Isaac Sim's deformables are currently passive and cannot be
  attached to rigid articulations, so a robot could not grip a deformable flap.
- Claiming ECT or BCT numbers. Those describe crushing, not folding, and we cannot
  crush anything yet. The McKee formula is recorded in the research note as a future
  validation target, not as a simulation input.

## User learning
Concept: a crease is not a hinge. A hinge returns; a crease gives way at a threshold
and is permanently weaker afterwards. That asymmetry is the whole behaviour, and it
is a rule we write, not something the physics engine provides.
Experiment: with Stage C running, fold one flap just under the yield torque and one
just over, then try to fold both again and compare the torque needed.

## Next action
Stage A only: add the flap table to `geometry.py` with unit tests proving
`flap_length == W/2` and that the outer flaps meet at the centre. Do not touch the
simulator in the first sitting.

User supplied full prompt saved contracts/carton_codex_prompt.md. Current implementation
uses installed Isaac 6 Articulation.set_dof_position_targets, per-degree USD gains
converted from radian config, viscoplastic internal state and estimated panel density.
jointFriction is dimensionless; orthotropic panel bending is not implemented.
First two physics runs produced USD/9600 rows but plastic/open-angle checks failed;
evidence runs/20260917T084748Z_ext1_carton and 20260917T084927Z_ext1_carton preserved.
Next diagnostic: external link torque loading with collisions retained.

Latest 105836Z: low-load major returns, high-load major plastic reference shifts; full
acceptance fail (minor obstruction, high major not settled). 132 offline tests pass,
7 skipped. Report reports/development/2026-09-17_codex_carton_prototype.md.
Next exact action: separate opening-order/isolated-crease diagnostics without editing
old gates or disabling collisions; full material prompt remains incomplete.

Opening-order diagnostic scope (2026-09-17): independent all-high-load scenario;
major flaps load 0–3 s, hold while minors load 3–6 s, all actuators off 6–20 s.
Frozen opening profile: every peak >60 deg, plastic reference >10 deg, final >10 deg,
final velocity <.02 rad/s. Retain legacy mixed-load checks and its failure unchanged.
Use solver iterations32/8, collision and self-collision on. This is a separate
interaction diagnostic, not replacement validation or measured cardboard properties.


## 20260917T114641Z: declared rigid-hinge proxy milestone verified

User full prompt supersedes initial top+bottom eight-flap plan: current requested fourTOPflaps and fixed bottom.
Geometry author, state model, runtime orchestration, validation and replay are now separate modules.
Opening/crease/cyclic diagnostic pass: 20260917T114330Z_ext1_carton, 20260917T114240Z_ext1_carton, 20260917T114414Z_ext1_carton.
PhysxJointAxisAPI friction .005Nm authored and tensor readback verified; all estimates.
Native41 rules pass + explicit defaultPrim negative; initialfailure retained.
Old mixed-load gate and low-control joint unchanged, fail retained, host1 intentional.
Full task stays in_progress: orthotropic panel bending and real material calibration not implemented/verified; IsaacLab/robot contact not_tested.
No MP4/camera render/human WebRTC claim. Reports contain one-stage commands and replay instructions.
Next exact action: real flap force-angle trace per calibration protocol; then identification/held-out validation, not guessed literature numbers.


## 20260917T120925Z: user requests live pulling/hitting

Bounded live interaction: Python PRE_PHYSICS_STEP crease callback, torque pulses, UI window and
manual Script Editor loader; no automatic animations, no other session stop.
Verified headless1208 callbacks/plastic states + UIconstruction120721Z.
NativeWebRTC mouse/render not_tested; boxfixed/boardsrigid, no crumple/tear claim.
Next exact action: human Shift-drag mainflap via script loader and record interaction result.

## 2026-09-17 MD/CD implementation

# Current state — 2026-09-17 MD/CD strip proxy

EXT1: directional segmented panel bending implemented and headless verified. Report: reports/development/2026-09-17_mdcd_panel_bending.md.
Run 20260917T121758Z_ext1_mdcd_bending: MD/CD analytic comparison and elastic return pass; 16-DOF carton live callback 968 samples, no error. Existing rigid carton acceptance unchanged; original mixed load still fail.
Native USD41 pass at 20260917T121839Z_ext1_panel_usd_check; unittest136/7skip exit0 at 121906; smoke121049 exit0.
Literature B-flute130TL data provenance preserved; material matching/calibration unknown. One-dimensional strip only: no 2D shell/torsion/in-plane deformation/crushing/fracture; walls/base remain rigid.
WebRTC human interaction/render/video not_tested. Manual entry scripts/carton_mdcd_editor.py. Earlier121636 misleading whole-run pass corrected by delivery audit;121714 fail preserved.
S5D still incomplete/paused; no claim whole workflow complete, official provider/keyboard/IsaacLab execution not tested.
Next action: fixed-profile time-step and segment-count sensitivity benchmark, no acceptance relaxation.

## 被動受力操作（使用者更正，2026-09-17）

# 最新狀態 — 2026-09-17 被動紙箱受力

EXT1進行中。使用者確認需求是外力／機器人接觸操作，沒有開關命令。新資產20260917T123830Z_ext1_independent_interaction拒絕drive-offset操作，材料回呼與外力工具分離，預設無操作UI／自動動作。
單片主蓋外力、逐片次蓋受力及估計板面塑性headless pass（exit0）；次蓋案例外力支撐主蓋。
20260917T123950Z_ext1_passive_contact碰撞手指exit0：單片主蓋94.77°，另一片绝对最大0.435°；量得接觸力峰值0.778875N；不是完整機器人。
原始混合載荷fail保留，舊四關節回歸123919 exit0。官方41規則123916 pass；136 tests7skip123857 exit0；smoke122729 exit0。
板材MD/CD來源保留；板面塑性降伏曲率2/m、鬆弛0.05s是估計，殘留形狀受±30°限位影響，未校準。固定底／剛性箱壁／一維板條，無完整殼、壓皺或破裂。
WebRTC原生拖曳仍未驗證（使用者舊版失敗）；headless已量測UI擴充false、pickingForce1.0，但viewer狀態未知。啟用本地UI擴充被自動批准審查拒絕，未執行；等待使用者明確例外批准。
入口scripts/carton_passive_editor.py。報告reports/development/2026-09-17_passive_carton_forces.md。render／影片未執行。S5D仍未完成；全工作流未宣稱完成。
下一步：獲准後以viewer唯讀診斷確認是否需要啟用本地滑鼠UI，再做原生拖曳驗證。

## Stage清理與外力模式

本輪更新：自有Stage／joint／view參考明確清理；重复UI復用，外力工具新增拉(+N)／壓(-N)／敲擊短脈衝。124624 headless4112步與清理通過；124700離線136/7skip exit0，smoke124447 exit0。入口scripts/carton_force_editor.py提供外部施力工具，無開關控制。原生鼠標仍未修復／未驗證，UI啟用例外仍待批准。報告reports/development/2026-09-17_force_tools_stage_cleanup.md。

## 編輯器匯入修正

# 最新狀態 — 2026-09-17 編輯器匯入入口修正

EXT1仍進行中，資產為被動受外力／接觸物件，無開關命令。
使用者viewer報carton_lifecycle缺失；本地檔存在，實際viewer根因unknown。入口檔案preflight、明確包搜尋路徑、invalidate caches與async異常取得已實作。
125101Z_ext1_editor_loader真正入口私有Kit測試exit0：故意stale包path仍載入成功、外力單片操作、二次載入成功。125024 smoke exit0；syntax/diff通過，報告reports/development/2026-09-17_editor_import_fix.md。
之前純外力124624及接觸123950 pass保留；原混合fail保留。MD/CD文獻板面剛度／估計塑性未校準，固定底、剛性箱壁、一維條模型與限位限制未改。
原生WebRTC mouse仍未驗證／使用者回報不動；UI啟用此前auto-review拒絕，例外尚未獲准且未執行。不宣稱render、人眼、真機器人或全流程完成；S5D未完成。
下一步：使用者在現有viewer重跑carton_force_editor.py，確認module search及READ-ONLY mouse diagnosis。


## 20260917T130752Z: settle 量測與 legacy gate 退役（使用者授權）

`settled` 改以最後 1 秒角度峰對峰值量測，容差 0.02 rad/s 不變；DOF 速度讀回在持續接觸下會保留舊值，
仍完整記錄於 settle_metrics 但不再當判準。legacy-mixed 標為 superseded_by_spec_error 退役：
壓住一片主蓋同時要求下方次蓋塑性張開，對 RSC 不可達；checks 照算照報，status 為 superseded 永不 pass，
pf-carton 對它仍 exit 非 0，舊 run 未更動。高低載對照由 crease-coupon 承接，pf-carton 預設改 opening-order。
實測：130538 opening-order pass、130614 crease-coupon pass、130641 crease-cyclic pass、130717 legacy-mixed superseded exit1。
130254 smoke exit0；unittest 145/7skip exit0。證據 runs/20260917T130752Z_ext1_settle_spec_delivery，D060，
報告 reports/development/2026-09-17_settle_metric_and_legacy_gate.md。
真實紙板校正、板面二維殼、render／影片／WebRTC 人眼仍 not_tested。
下一個精確動作：依 CARTON_CALIBRATION_PROTOCOL 量一片真實主蓋的 force-angle 曲線，反推 stiffness/yield/viscosity。


## 20260917T132321Z: 手感三項缺陷的量化修正（使用者回報）

新增 carton_feel.py（純離線）把 config 換算成手可以感覺到的量：降伏角、尖端開啟力、殘餘力矩對自重比、
塑性速率上限、分段板 omega*dt。舊互動資產量到降伏角 43°、塑性速率 0.123 rad/s 且與拉力無關、
殘餘力矩為自重 5.35 倍、分段板 omega*dt=24.9（可積分上限約 0.3）。
修正：crease_model 允許黏度 0（即其 backward Euler 本來就內含的率無關 return map）；
摺痕參數改由 derive_carton_creases 從「回彈幾度」「摺過後是否撐得住自重」反推，並依摺痕長度縮放；
互動資產改剛性板；author_segmented_carton 預設拒絕不可積分的分段勁度，legacy 模組以 'record' 保留舊證據。
新量測 scripts/pf-carton-pull：0.16N 開始開、0.30N 到 60°、79.4° 放手停 73.8°（回彈 5.6°）、
1N×0.4s 留下 98° 永久摺角、0.05N 小力探測彈回且塑性參考角 bit 不變、鄰片未被帶動。
20260917T132321Z_ext1_carton_pull exit0；編輯器入口已改指此資產，pf-carton-editor-test 132446 exit0。
回歸：interaction-test、panel-bending-test、smoke、unittest 157/7skip 全 exit0。
所有參數仍為 uncalibrated_assumption；原生滑鼠拖曳、render、人眼仍 not_tested。
下一個精確動作：依 CARTON_CALIBRATION_PROTOCOL 量真實主蓋的 force-angle 曲線，用它取代推導目標。


## 20260917T133338Z: 滑鼠拉不動 — 力臂與 pickingForce（使用者回報）

讀本機 omni.physx 110.1.13：拖曳力縮放為 /physics/pickingForce，使用者 app 讀回預設 1.0，
官方 KaplaArenaDemo 設 10。安裝包未定義每單位等於多少牛頓，且無可程式 grab API，
因此滑鼠實際送出的力無法 headless 量測，仍 not_tested。
可量的是資產需要多少力：關著的主蓋外緣 0.141N（降伏 0.00841 + 自重 0.00561 N·m ÷ 0.0995m），
與 ramp 實測 0.16N 一致；中點需 2 倍、靠摺痕 1/4 處需 4 倍。
夾擊驗證（MinorXN 中點）：0.7 倍預測力只動 1.6°，1.3 倍開到 49.7°。
提供三個做法：抓外緣、mouse_mode('joint') 用約束拖曳（不受 pickingForce 影響，載入時預設）、
grab_strength(20) 讀寫 /physics/pickingForce 並印出原值還原。摺痕參數未更動（D061）。
20260917T133338Z_ext1_carton_pull exit0（18 checks）；editor-test 133412 exit0；unittest 160/7skip；smoke 133429 exit0。
下一個精確動作：使用者回報三個做法後的結果；平行進行真實主蓋 force-angle 量測取代 0.141N 預測。


## 20260917T134614Z: 滑鼠拖曳的四道閘門（使用者 pickingForce 1000 仍無效）

pickingForce 1000 無效即排除力量大小。讀 omni.physx.ui 110.1.13 原始碼，
on_mouse_shift_drag_start 需依序通過：擴充在跑且持有 viewport overlay、timeline 播放中、
整段拖曳按住 Shift（或 _mouse_interaction_state=ENABLED）、無其他 gesture/hover 佔用游標（選取 gizmo 會佔用），
之後才呼叫 get_physx_interface().update_interaction，pickingForce 才生效。
程式化驅動該 API（20260917T134614Z_ext1_native_grab）：無 POINT_GRABBED，地面對照方塊僅位移 2e-8 m，
因 standalone app 的 omni.physx.ui 關閉；記為 blocked 並寫 blocked.json，不證明使用者 GUI viewer 的行為。
未歸因觀察保留：pickingForce 1000 時 MajorYP 曾瞬間 100° 但無 grab 事件。
carton_mouse_diagnostic 改為回報四道閘門與 blockers（唯讀）；LiveCarton.mouse_no_shift() 呼叫擴充自身公開覆寫；
編輯器入口載入時印出完整診斷。native-grab exit4、editor-test 134525 exit0、unittest160/7skip、smoke134634 exit0。
下一個精確動作：使用者回報載入時印出的 blockers 內容，再決定是操作面（Shift/gizmo/抓取點）或需要啟用擴充的例外。


## 20260917T140926Z: 推關保持與推/拖曳不對稱（使用者回報）

使用者：滑鼠推有效、拖曳無效；推關之後又彈開。
推有效即證明其 viewer 的 omni.physx.ui 已啟用（D063 第一道閘門通過），剩餘嫌疑為選取 gizmo 佔用拖曳手勢與 Shift。
安裝預設不對稱：/physics/mousePush=1000 對 /physics/pickingForce=1.0，且點擊不與 gizmo 競爭而拖曳會。
回彈：使用者陳述的規則（小角度恢復、超過降伏留下）正是本模型的定義。目前資產量不出「推關又彈開」：
其他三片關閉時，摺開 96.9° → −1N 推回 −0.34° → 放手仍 −0.34°，回彈 0.00002°，塑性參考角重設 2.08°。
第一次量測被污染並保留：四片全開時主蓋走 11° 即卡在 85.5°（撞到立起的次蓋，是干涉非回彈），該兩項 fail 為測試設計問題。
順序已改為其他蓋關閉時做推測試，並在次蓋階段前重新打開主蓋。
舊資產 segmented_directional_strip_v1 回彈 43.0°，新 rigid_panel_v1 為 4.0°，推測使用者仍在舊資產上。
LiveCarton 載入時改為印出 panel model／回彈角／邊緣力，>15° 另印 WARNING。
pf-carton-pull exit0（23 checks）；editor-test 141003 exit0；unittest160/7skip；smoke141032 exit0。
下一個精確動作：使用者重新載入並回報「Loaded asset」那一行與 blockers。


## 20260917T141734Z: resident stage 警告無法重現，記為未解釋

使用者截圖的警告指向前一個資產（133338Z），即換資產的瞬間。
editor loader test 已改為真正換資產（跑真入口於 A，再跑於 B）並掃描擷取到的 Kit log：
警告未出現，swap 完成，前一個 controller 的 stage 為 None。
拿掉新加的 gc.collect() 的對照組同樣沒有警告，故該 collect 標註為未經證實的預防措施而非已證實修正。
剩餘差異屬 GUI 專有：選取中的 prim 會被 selection 與 property window 持有，私有 Kit 沒有這些。
入口改為在開新 stage 前清除自身選取（可用點擊還原），同時移除 D064 中吞掉拖曳手勢的 gizmo；
此為合理推測而非有證據的修正。該警告描述清理而非失敗，與拉／推蓋子的行為無關。
editor-test 20260917T141734Z_ext1_editor_loader exit0（含 stage_swap_completed 與 no_resident_stage_on_swap）；unittest160/7skip；smoke141755 exit0。


## 20260917T143848Z: 摺痕上限 179° 與可自由站立的箱體（使用者回報）

使用者：只能開到約 90° 就卡死；拉整個箱體不會動。兩者都是我們寫死的限制。
(1) 關節上限原為 100°，改為可設定並採用 −5°～179°（摺痕長在牆外表面，180° 恰好貼平，留 1° 避開退化姿態）。
實測主蓋翻到 179.0°，放手停 179.0°，塑性參考 176.5°。
(2) 底部原有 FixedJoint 釘在世界；新增 base_mode=fixed|free，free 移除該 joint 並加地面板。
base 質量改由板材面密度計算（底＋四牆）=0.0846kg，不再是手填 0.2kg。
自由箱體實測：側向力掃描 0.7N 開始滑動（隱含 μ=0.84，為模擬器預設材質非我方宣告），
用 0.25N 拉蓋子箱體位移 2.3e-8m。作廢並保留的兩次亂猜推力：0.5N 不動、20N 飛 33m。
editor loader test 原用 2N（自由箱體自重 0.83N 的 2.4 倍）把整箱丟飛、四蓋全開；
已改用實測 0.30N 並新增 box_not_shoved_by_one_flap（實測 1.3e-8m）。
pf-carton-pull 固定底 143848Z exit0（28 checks）、自由底 143819Z exit0；editor-test exit0；unittest160/7skip；smoke143935 exit0。
入口已指向自由箱體資產。下一個精確動作：宣告板材與地面的 physics material，使摩擦係數為我方估計值而非模擬器預設。


## 20260917T150421Z: 完全打開是 270° 不是 180°（使用者更正，我上一輪判斷錯誤）

D066 說 179° 貼平外牆是錯的。繞摺痕軸：0° 關閉、90° 直立、180° 水平外伸如棚板、270° 沿外牆垂下。
270° 時板厚方向朝內，故板子改為相對摺痕軸往外偏移 t/2，鉸鏈高度各抬一個板厚維持關閉堆疊
（次蓋 H+t、主蓋 H+2t）。上限改 270。
實測 20260917T150421Z：翻到 270.0°、放手停 268.97°（牆-蓋夾角 358.97°，關閉為 90°）、
尖端在鉸鏈下方 99.5mm（等於蓋長，完全下垂）、離牆面外側 1.79mm。固定底 30 checks 全過；自由底 150447Z 6 checks 全過。
另修兩處：opposite_minor_undisturbed 原用 abs()<5 與未被碰蓋子停在 −5° 下限剛好相等而誤判，改為判斷是否被打開；
先前宣稱 joint drag「用約束拖曳」無根據，安裝包僅說明設定名為 SETTING_MOUSE_GRAB_WITH_FORCE 且該力由 pickingForce 縮放，
另一模式機制在封閉二進位中，程式說明已更正。
editor-test 150513 exit0；interaction-test exit0；unittest160/7skip；smoke150536 exit0。入口指向 150447Z。
下一個精確動作：宣告板材與地面 physics material（摩擦仍為模擬器預設 0.84）。


## 20260917T151929Z: 匯出包與 USD 物理邊界（使用者要求）

使用者要求：移除 joint drag（只抓得到整箱）、移除四個外緣施力欄位、存一個暫存、說明如何輸出給他人及物理是否在 USD 裡。
移除 joint drag 與四個施力欄位 UI（ForceProbe 類別保留供 headless 量測）。
新增 scripts/pf-carton-export 與 carton_export_check.py：產生 exports/<name>/ 並在 Isaac 內開啟匯出的 USD 讀回物理。
讀回確認存在：articulation root、9 片碰撞板、4 個 revolute（−5～270 限位）、角度驅動勁度換算回 0.1204 N·m/rad 四片全符、
阻尼／靜止角／力上限、joint friction 與摩擦力矩、剛體質量、PhysicsScene 與重力。
確認不在 USD：摺痕降伏力矩、塑性黏度、軟化率（USD 驅動只有一個靜止角屬性，永久摺痕需逐步移動它），
故單獨開啟 USD 時摺痕為彈性。包內附 crease_controller/ 六個模組與 load_in_isaacsim.py。板面變形完全未模擬。
抓到兩個 bug：carton_usd_check 仍硬寫 −5/100 限位（改讀 config）；讀回迴圈變數遮蔽蓋子名稱導致勁度比對被靜默跳過。
export 151929Z exit0；editor-test exit0；unittest160/7skip；smoke151955 exit0。未 git commit（工作樹有大量既存未追蹤檔案，待使用者決定）。
下一個精確動作：使用者決定是否 git commit 暫存；之後為板面凹陷／破壞選定方法（分段降勁度、deformable、或損傷代理）。


## 2026-09-18 規劃補充（未實作）

依使用者要求先整理泛用工作流：`docs/plans/2026-09-18_task_driven_asset_workflow.md`。
現有剛板／塑性摺痕狀態不變；不將早期 commanded fold 或限位描述當作被動資產的新驗收。
下一步先完成 P0 需求契約與缺口表，再決定板面變形能力卡。

網路調查補充：`docs/research/2026-09-18_asset_generation_landscape.md`。保留現有物理狀態，通用流程依部件／接合／能力組合，外部生成器尚未實測。

完整規劃入口已整理為 `../plans/2026-09-18_general_asset_workflow_master_plan.md`；下一張待執行為 WF-P0。EXT1 物理能力不變，本次未實作。
