# pickingForce 1000 沒有反應，代表問題不在力的大小

你把抓取強度調到 1000 仍然拉不動，這本身就排除了「力太小」。
讀本機安裝的 omni.physx.ui 110.1.13，一次 viewport 拖曳要通過**四道閘門**才會碰到 PhysX
（`PhysxUIViewportOverlays.on_mouse_shift_drag_start` 依序 return）：

1. `omni.physx.ui` 這個擴充有在跑，而且持有 viewport overlay；
2. **timeline 正在播放**（暫停狀態直接 return）；
3. **整個拖曳過程按著 Shift**，除非 `_mouse_interaction_state` 被設成 ENABLED；
4. 沒有其他 gesture／hover 佔用游標——**選取後的移動 gizmo 就會佔用**。

四道都過了，才會呼叫 `get_physx_interface().update_interaction(ray, event)`，
`pickingForce` 也才有意義。它是最後一道，不是第一道。

## 我實際去驅動了那個 API

`update_interaction` 可以用程式呼叫，所以我在 headless 直接驅動它
（[20260917T134614Z_ext1_native_grab](../../runs/20260917T134614Z_ext1_native_grab)）。結果是
**完全沒有附著任何抓取**：沒有 POINT_GRABBED 事件，連放在地面上的普通對照方塊都只位移 2e-8 m，
即使三個互動設定全開。原因就是第 1 道閘門——standalone app 裡 `omni.physx.ui` 是關閉的。

所以這個 run 記為 **blocked 不是 fail**，並寫了 blocked.json：沒有互動子系統可驅動，
它也就無法證明你那個有 GUI 的 viewer 會怎樣。有一項觀察我保留為未歸因：
pickingForce 1000 時 MajorYP 曾瞬間衝到 100°，但沒有任何 grab 事件，我不拿它當證據。

## 你這一步只要跑一行

先存檔、停止 timeline，重新載入入口（現在會自己印出完整診斷）：

```python
exec(open("/mnt/HDD4/wyattsheu/ITRI/parcel-forge/scripts/carton_force_editor.py").read())
```

看印出來的 `blockers`：

- **blockers 是空的** → 四道閘門都通了，問題在操作：整段拖曳按住 **Shift**、先點空白處取消選取避免 gizmo 搶走游標、抓在蓋子**外緣**。
  嫌 Shift 麻煩就呼叫 `pf_live.mouse_no_shift()`，之後左鍵直接拖。
- **blockers 說 `omni.physx.ui is not enabled`** → 你的 app 根本沒有物理滑鼠互動，`pickingForce` 調到多少都沒用。
  要修就得啟用那個已安裝的擴充，那正是先前被自動審查擋下、仍需要你明確批准的例外。

把那段 `blockers` 貼給我，我就能直接往下做。

## 驗證與限制

`./scripts/pf-carton-native-grab` exit 4（blocked，附 blocked.json）；editor-test 134525 exit0；
unittest 160/7skip exit0；smoke 134634 exit0。診斷是唯讀的，沒有啟用、設定或安裝任何東西。
`mouse_no_shift()` 呼叫的是該擴充自己的公開覆寫函式，擴充不在時只會印訊息並回傳 False。
原生滑鼠拖曳仍 not_tested。已驗證可用的施力方式仍然是 UI 上那組外力工具。
