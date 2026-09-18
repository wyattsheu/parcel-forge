# 推得動、拉不動；以及推關之後會不會彈開

## 一、推有效、拖曳無效，這兩件事的答案不同

安裝的預設值本身就不對稱：`/physics/mousePush` 是 **1000**，`/physics/pickingForce` 是 **1.0**。
預設的推，尺度是預設的拉的一千倍。

而且**推是點擊，拖曳是拖曳**。`on_mouse_shift_drag_start` 在
`get_active_gesture() or get_active_hover()` 有值時直接 return——選取後的移動 gizmo 就會佔住拖曳手勢，
但它不會跟點擊搶。

**你的推有效，反而證明了一件好事**：`omni.physx.ui` 在你的 viewer 裡是啟用的，
D063 的第一道閘門在你那邊是通的。剩下的嫌疑只有兩個：gizmo 佔用游標、以及 Shift。
所以先點空白處取消選取（或按 Esc）再拖；或呼叫 `pf_live.mouse_no_shift()`。

## 二、你講的回彈規則是對的，而且模型就是這樣寫的

小角度彎折會恢復、超過降伏的摺痕會留下——這正是彈塑性摺痕的定義，也是這個資產在做的事。

但你描述的「推到合起來又彈開」，在目前資產上量不出來。
[20260917T140926Z_ext1_carton_pull](../../runs/20260917T140926Z_ext1_carton_pull)，其他三片全部關著時：

| 步驟 | 量到 |
| --- | --- |
| 拉開並摺出永久角 | 96.9° |
| 用 −1 N 推回關閉 | −0.34°（完全關上） |
| 放手靜置 3 秒 | **−0.34°，回彈 0.00002°** |
| 摺痕塑性參考角 | 重設為 2.08° |

**推關就關著，沒有彈開。**

第一次量這件事我量壞了，證據保留：當四片蓋全部立著時，被推的主蓋走了 11° 就**卡在 85.5° 完全不動**——
那是撞到立起來的次蓋，是干涉不是回彈，那兩項 fail 是我的測試設計問題。
現在的順序改成在其他蓋關閉時做推的測試，並在測次蓋之前先把主蓋重新打開（RSC 的次蓋在主蓋底下，主蓋關著就會壓住它們）。

## 三、所以你手上很可能還是舊資產

| 資產 | 摺痕回彈 |
| --- | --- |
| `segmented_directional_strip_v1`（舊） | **43.0°** |
| `rigid_panel_v1`（現在這個） | **4.0°** |

43° 的回彈，正好就是你形容的「推回去又彈開來」。
載入時現在會直接印出這一行，不用去翻 config：

```
Loaded asset: rigid_panel_v1, springback 4.0 deg, 0.085 N at the flap edge to crease it
```

如果印出來是 `segmented_directional_strip_v1` 或 springback 大於 15，會另外跳一行 WARNING。
重新載入（先存檔、停 timeline）：

```python
exec(open("/mnt/HDD4/wyattsheu/ITRI/parcel-forge/scripts/carton_force_editor.py").read())
```

## 驗證

`./scripts/pf-carton-pull` exit 0，23 項 checks 全過（含推關保持、推的期間其他蓋確實關著、主蓋可重新打開）。
editor-test exit0；unittest 160/7skip exit0；smoke exit0。
仍未驗證：原生滑鼠拖曳、真實紙板校正（4° 回彈與 0.085 N 都是推導目標，不是量過真紙箱）。
