# 即時互動纸箱：WebRTC 拉動／推擊

使用者指出 recording.usda 只能回放。已新增 carton_live.py，掛接 Isaac6 PRE_PHYSICS_STEP，
每步讀回角度、更新彈塑性參考角，讓外力操作後繼續有回彈／殘餘角／模型軟化。
新增操作面板、可指定力矩脈衝；没有預錄動畫驅動，也沒有位置瞬移。
本檔是**建置進度**；真實執行證據另存 reports/execution/2026-09-17_live_carton_interaction.md。

## 在既有 WebRTC 使用

先儲存目前工作，停止timeline。不要開recording.usda；在Script Editor執行以下整段：

```python
import sys, asyncio, omni.usd
sys.path.insert(0, "/mnt/HDD4/wyattsheu/ITRI/parcel-forge/src")

async def _pf_start_live():
    global pf_live
    if "pf_live" in globals():
        pf_live.close()  # 只卸除本工具的回呼與面板
    ok, error = await omni.usd.get_context().open_stage_async(
        "/mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260917T114330Z_ext1_carton/asset.usda"
    )
    if not ok:
        raise RuntimeError(error)
    from parcel_forge.carton_live import attach
    pf_live = attach("20260917T114330Z_ext1_carton")

_pf_live_task = asyncio.ensure_future(_pf_start_live())
```

等待 `Parcel Forge - Live carton` 面板出现，選取 `/World/Carton/MajorYN`、按F定位，再按Play。
面板 `Mouse: grab`：Shift＋左鍵按住上蓋拖曳，放手看回彈。
面板 `Mouse: push`：Shift＋左鍵對蓋片推擊。不是W移動工具；W改的是建模位置，不能當作施力測試。

一個概念：現在蓋子的運動來自即時物理，放手後仍由折痕模型處理。
一個實驗：同一片主蓋先輕拉再放手，再拉更大的角度放手；只改最大拉開角，觀察残餘角。
被另一片蓋擋住時，先開兩片主蓋；不要把碰撞阻擋當作程式沒有反應。

若滑鼠操作未生效，可先按 `Open both major flaps (3s torque)` 驗證回呼／物理。
這是3秒0.08Nm外力矩測試，不是動畫。接著可以直接用滑鼠操作次蓋。
在Script Editor檢查：

```python
print("physics callback samples:", pf_live.samples, "failed:", pf_live.failed)
print("evidence:", pf_live.out)
# 額外對次蓋施加短暫力矩；必須timeline正在Play
pf_live.push("MinorXN", torque_nm=0.08, seconds=0.2)
# 切換回抓取
pf_live.mouse_mode("grab")
```

samples應持續增加；failed=True時讀 pf_live.out/events.jsonl 的錯誤。
Pause保留當前塑性歷史，Stop讓控制器重設到初始asset參考狀態。
換stage前執行 `pf_live.close()`；不會關閉viewer或停止其他程序。
控制器不代替使用者播放timeline，也不自動載入／覆寫stage；載入是上述使用者執行的Script Editor步驟。

## 重跑驗證

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf-carton-live-test
```

獨立headless程序，先檢查GPU資源，livestream disabled，不觸碰既有viewer端口。
120600Z測試：1208次物理回呼、兩主蓋塑性參考角約0.8104rad、pass；
UI construction與native mouse／WebRTC成功要分別記錄，headless測試不能替你確認滑鼠。

## 方法來源／限制

- [NVIDIA Isaac6.0.1 Simulation Fundamentals](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/physics/simulation_fundamentals.html)：播放時Shift＋左鍵物理互動。
- [NVIDIA Mouse Interaction](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/extensions/ux/source/omni.physx.ui/docs/dev_guide/sim_management.html)：Mouse Grab與push模式。
- [NVIDIA Physics Settings](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.0/dev_guide/settings.html)：mouseInteractionEnabled、mouseGrab、forceGrab。UX/settings文件版本較舊，WebRTC實際滑鼠路徑仍待人類確認。
- **版本匹配本機源碼**：Isaac6.0.1 SimulationManager.register_callback(PHYSICS_PRE_STEP)，callback(dt,context)，以及Articulation角度讀回／目標寫入。
- **本專案實作**：LiveCarton生命週期、沿用黏塑性代理模型、力矩等效drive offset、脈衝控制與逐步事件紀錄；不是NVIDIA內建紙板材料模型。

箱體固定，板面是剛性板件：可拉／推蓋子、碰撞、回彈，但箱面不會被捶凹、裂開或折皺。
材料估計、MD/CD板面彎曲／實物校準仍未完成。任何WebRTC操作成功只能由使用者確認。

## 一行載入方式

先儲存工作並停止timeline，在Script Editor執行：

```python
exec(open("/mnt/HDD4/wyattsheu/ITRI/parcel-forge/scripts/carton_live_editor.py").read())
```

與上面完整步驟相同，不啟動新的viewer。頭less面板建立及callback最新重驗pass：
`20260917T120721Z_ext1_live_callback_test`（1208步）；native滑鼠／WebRTC仍not_tested。
syntax／diffcheck證據：`20260917T120925Z_ext1_live_delivery`。


## 被動操作需求更新

本文件原先開蓋操作說明由 reports/development/2026-09-17_passive_carton_forces.md 取代；不再提供開／關按鈕。原run與結果保留。原生WebRTC未宣稱修復。
