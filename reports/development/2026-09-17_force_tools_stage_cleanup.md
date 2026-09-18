# 拉、壓、敲擊工具與 USD Stage 清理

使用者回報 reference count2 及原生拖曳仍失效。警告表示關閉時仍有Stage參考；不能單憑警告判定力學卡死。
已確認parcel-forge舊close保留Stage／joint／view，且Isaac6 Prim內部回呼強引用自身。新版明確解註冊**自己建立的view**回呼、釋放joint／Stage；不是重設SimulationManager或關閉其他程序。
Loader先清理舊版控制器的已知自有參考，再close並開新場景，且reload工具模組，避免viewer沿用沒有敲擊按鈕的舊Python類別。
重複show_controls不建立第二個視窗／力工具。原生WebRTC未宣稱修復。

## 操作

存檔、停止timeline，Script Editor：

```python
exec(open('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/scripts/carton_force_editor.py').read())
```

等待載入完成，再Play。選 `/World/Carton/MajorYN_S3`、F定位。
每列是單片蓋的**外部力工具**，沒有開／關狀態：

| 操作 | 工具用法 | 物理意義 |
|---|---|---|
|拉|MajorYN edge force設+2|外緣沿当下板段法線持續2N|
|壓|同欄設-2|相反方向持續2N；閉合蓋受到下方蓋的碰撞支撐，不會穿透|
|敲擊|該列Hit 10N / 0.05s|向內-10N、0.05秒力脈衝，標稱衝量-0.5N·s；不是直接設定物件速度|
|放手|設0或Release test forces|停止外力，由重力／材料力／接觸決定後續姿態|

單一實驗：只把MajorYN從0改+2N，驗證單片受力；再設0看回彈／殘留角。小力仍可彈回，塑性是估計模型不是所有拉動必留下變形。
敲擊替換該片原持續力，數值欄清0、脈衝後停止。次蓋被主蓋遮擋時仍需物理支撐／移開主蓋，不使用開關指令解鎖。
此工具只能沿外緣當下法線施力，不是任意滑鼠點拖曳，不是壓板機／材料強度試驗。資產仍固定底、剛性箱壁、一維分段板，沒有整箱揉皺破裂。
機器人運行僅載入材料callback，這個力工具可完全不載入。

## 原生滑鼠模式

Mouse: grab／push按鈕僅請求原生滑鼠拉／推模式。原生UI擴充是否啟用與WebRTC輸入是否傳到引擎仍未知，不能當作按鈕存在就可用。
Loader的READ-ONLY mouse diagnosis印出目前viewer擴充／係數。先前headlessUI全false、pickingForce1.0，不能推出viewer也是如此。
set_extension_enabled_immediate啟用UI先前被自動批准審查拒絕，引用AGENTS no-reconfigure；仍未啟用，待使用者批准僅啟用本地UI的例外。不安装／升級／重啟或改設定檔。

## 證據

- ./scripts/pf smoke --physics-only：exit0，20260917T124447Z_s1_smoke。
- ./scripts/pf-carton-interaction-test：exit0，20260917T124624Z_ext1_independent_interaction。單片拉力、各片受力、估計塑性、重複UI復用、短脈衝結束與清理欄位皆通過；4112回呼。
- 20260917T124624Z_ext1_independent_interaction/result.json cleanup：stage/view/joints皆釋放、自有callback移除。只證明我們的參考釋放，不保證viewer所有參考與警告都消失。
- 脈衝執行測試使用-1N／.05s；UI已建構10N按鈕，但真正點擊按鈕與10N人眼結果未驗證。
- 離線136 tests，7 skipped，exit0，20260917T124700Z_ext1_interaction_tools_checks。diff0。
- 先前純碰撞單片95°與0.778875N結果仍保留123950，但本次不是新機器人驗證。
- render／video未執行；原生mouse與WebRTC人眼新版本not_tested。

程式清理API依本機isaacsim.core.experimental.prims.Prim._deregister_callbacks與weak timeline subscription實作。私有方法僅對自有包裝器使用，未清空全域回呼。
下一步：使用者批准UI例外後，按viewer唯讀診斷確認需要的擴充與原生拖曳；沒有批准就只使用外部力工具。
