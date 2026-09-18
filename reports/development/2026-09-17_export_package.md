# 怎麼交給別人，以及物理性質到底在不在 USD 裡

## 先回答最重要的：大部分在，但**讓它是紙箱的那部分不在**

`./scripts/pf-carton-export --run <run-id> --name carton_v1` 會產生 `exports/carton_v1/`，
而且會**真的打開匯出的 USD 把物理讀回來**，不是憑空宣稱。

**確認存在於 `carton.usda`（讀回驗證）**：

- 一個 articulation root、九片可碰撞板
- 四個 `PhysicsRevoluteJoint`，含轉軸與 **−5°～270°** 限位
- 角度驅動：每度勁度換算回來正好是設定的 **0.1204 N·m/rad**（四片全對），以及阻尼、靜止角、力上限
- PhysX joint friction 與靜／動摩擦力矩
- 剛體質量、PhysicsScene 與重力

**不在 USD 裡**（`physics_in_usd.json` 與 README 都明講）：

| 缺的東西 | 為什麼 |
| --- | --- |
| 摺痕降伏力矩 0.0084 N·m | USD 的驅動只有**一個**靜止角屬性 |
| 塑性黏度、軟化率 | 「讓摺痕變成永久」是每個物理步去移動那個靜止角，USD 沒有這種屬性 |

**所以單獨打開那個 USD，你會得到一個關節箱子，但摺痕是彈性的——推開就彈回去。**
要有永久摺痕，必須跑包裡的 `crease_controller/load_in_isaacsim.py`。

## 包裡有什麼

```
exports/carton_v1/
  carton.usda              資產本身
  config.json              全部參數與 provenance
  physics_in_usd.json      讀回驗證：USD 真正帶了什麼、缺什麼
  README.md                給對方看的說明
  manifest.json            每個檔案的 sha256
  crease_controller/
    load_in_isaacsim.py    貼進 Script Editor 就能跑
    parcel_forge/          摺痕規則所需的六個模組
```

## 為什麼用力敲不會凹、不會壞

因為**板面是剛體**。目前整個資產裡唯一會變形的是**摺痕線**，板子本身不會凹陷、挫曲或破裂，
敲多用力都一樣。這是刻意的取捨，不是 bug：先前用分段條模擬板面彎曲時，那塊板材的勁度在
dt=1/240 下 ω·dt 高達 24.9（可積分上限約 0.3），條狀片只會抖動亂彈（見 D061）。

要做到「敲下去會凹」，需要下列其中之一，都不是小改動：

1. **降低分段勁度或加大子步數**，讓分段板進入可積分範圍，並重新驗證；
2. **deformable body**：Isaac 的 deformable 目前是被動的，無法掛在剛體 articulation 上，機器人抓不住；
3. **損傷代理**：偵測衝擊後把該處換成已凹陷的幾何——便宜但不是真力學。

我沒有動手做，因為這超出你這次的要求範圍。

## 本輪還做了

- 移除 joint drag（它只抓得到整箱，抓不到蓋子）
- 移除視窗裡那四個外緣施力欄位（ForceProbe 類別保留，headless 量測還在用）

順帶抓到兩個 bug：`carton_usd_check` 還在檢查舊的 −5/100 限位（改為讀 config）；
讀回程式的迴圈變數把蓋子名稱蓋掉，導致勁度比對被靜默跳過。

## 驗證

export exit0（四個關節、勁度與 config 全部相符）；editor-test exit0；unittest 160/7skip exit0；smoke exit0。
