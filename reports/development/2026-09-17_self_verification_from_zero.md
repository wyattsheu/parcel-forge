# 從零到現在：逐項自行驗證清單

這份清單供你逐個小成功點驗證，不需要一次重跑全部。
日期：2026-09-17。S0–S4 已有成功證據；S5 只完成合約格式，修復執行尚未完成。

## 開始前與 WebRTC 共通操作

所有指令先執行：

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
```

每項有「重新執行」和「看已保存場景」兩種操作。前者會產生新的 runs 目錄；
下面固定 run-id 指向已保存的歷史證據。要看你剛執行的結果，把 view 的 run-id
換成終端輸出的 `run:` 最後一段。模擬指令逐個執行，前一個結束再做下一個。

WebRTC 指令由你在主機終端執行。看到 `[VIEW] READY` 後，用現有 WebRTC client
連 `140.113.203.85:49100`（stream port 47998）。這是 client 的連線位址，不是
可直接貼到瀏覽器的網頁 URL。若你的 client 已設定另一個可達位址，沿用該設定，
並對 view 加 `--public-ip <該主機位址>`。

一次看一個場景；看完在啟動 viewer 的終端按 Ctrl+C 再換下一個。
這份清單不會自動停止已有 viewer。若顯示 port busy，先由你確認現有 viewer 的用途。
需要切換你自己的 parcel-forge viewer 時，可由你把 `view` 改為 `view --replace`。

`--ui` 顯示 Stage tree 與 Properties。若物件太小，選取 Box／Probe／Cube 後按 F
聚焦；可用上方暫停按鈕停止 viewer 的即時模擬。`scene_final.usda` 是最終姿態，
不是逐幀重播；viewer 會開啟新一輪即時物理，預設 dt=1/120，不能把新畫面當成
原驗收 dt=1/240 的軌跡。`asset.usda`（S2）是起始場景，可用 60 秒等待連線再放下 probe。

每次自己檢查後，填「未確認／成功／失敗」，不要把這份清單的歷史 pass 當成
你已做過的 WebRTC 確認。數學、錯誤分類與參數精度必須看終端，畫面只輔助。


## 01．環境版本與啟動路徑盤點

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf doctor
cat docs/ENVIRONMENT.md
```

成功條件：doctor exit 0；Isaac Sim 6.0.1.0 與既有 venv 路徑吻合，不安裝任何套件。

WebRTC：不適用。這一項應在終端確認；沒有可顯示該判定的模擬場景。

來源：本專案 S0、docs/ENVIRONMENT.md；環境數值是本機盤點。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 02．每次執行保留獨立證據

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf runs --last 10
cat runs/20260917T000114Z_s1_smoke/manifest.json
```

成功條件：看到不同 run-id、exit_code、輸入雜湊與 evidence 路徑。

已保存證據：`runs/20260917T000114Z_s1_smoke/manifest.json`。

WebRTC：不適用。這一項應在終端確認；沒有可顯示該判定的模擬場景。

來源：NVIDIA USD Content Agents 的工作流／工具分離影響；append-only 格式為本專案設計，連結見 docs/METHODS.md。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 03．地板與剛體方塊成功建立

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf smoke --physics-only
```

成功條件：runtime 與 pf exit 0，600/600 steps；產生 scene_final.usda。

已保存證據：`runs/20260917T004549Z_s1_smoke/`。

WebRTC：

```bash
./scripts/pf view --run 20260917T004549Z_s1_smoke --scene scene_final.usda --ui
```

畫面確認：地板上有一個小方塊，不是只有地板。這是落地後場景，不是自由落體影片。

來源：本專案案例與判定；方法依 docs/METHODS.md 及本機 Isaac Sim 6.0.1 API。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 04．自由落體與半隱式 Euler 參考

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
python3 -m unittest tests.test_free_fall_reference -v
cat runs/20260917T004356Z_s1_smoke/summary.md
```

成功條件：解析位移 0.04905 m；模擬約 0.05109 m，差 0.00204 m，在既定 0.003 m 門檻內。

已保存證據：`runs/20260917T004356Z_s1_smoke/trajectory.csv`。

WebRTC：

```bash
./scripts/pf view --run 20260917T004549Z_s1_smoke --scene scene_final.usda --ui
```

畫面確認：只能確認最後落地；不能從此畫面驗證 2.04 mm 的解析誤差。

來源：經典自由落體與半隱式 Euler；dt 和門檻為專案工程設定。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 05．姿態與速度成功讀回、沒有非有限數值

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
python3 -m json.tool runs/20260917T004356Z_s1_smoke/s1_result.json
```

成功條件：readback.status=ok、S1.no_nan=pass；讀回欄位含位置、四元數、線速度與角速度。

已保存證據：`runs/20260917T004356Z_s1_smoke/s1_result.json`。

WebRTC：

```bash
./scripts/pf view --run 20260917T004549Z_s1_smoke --scene scene_final.usda --ui
```

畫面確認：看得到方塊的讀回最終姿態；完整數值仍看 JSON／CSV。

來源：本專案案例與判定；方法依 docs/METHODS.md 及本機 Isaac Sim 6.0.1 API。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 06．方塊落地、沒有穿過地板、最後穩定

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf smoke --physics-only
```

成功條件：S1.cube_rests_on_ground、S1.no_tunneling、S1.settled 都 pass；中心 z 約 0.020 m。

已保存證據：`runs/20260917T004549Z_s1_smoke/`。

WebRTC：

```bash
./scripts/pf view --run 20260917T004549Z_s1_smoke --scene scene_final.usda --ui
```

畫面確認：方塊停在地板表面，沒有埋進去；速度門檻要看終端。

來源：本專案案例與判定；方法依 docs/METHODS.md 及本機 Isaac Sim 6.0.1 API。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 07．離線 PNG 可生成且非空白

歷史驗證：舊 run 非空白 PNG 成功；另有新 render 失敗，逐 run 分開記錄。

重新執行：

```bash
./scripts/pf smoke
xdg-open runs/20260917T004356Z_s1_smoke/renders/scene_final.png
```

成功條件：本次若成功應有 S1.render_png_not_blank=pass。保存的舊成功 PNG 是非空白；新 run 若崩潰必須記 fail，不能沿用舊 pass。

已保存證據：`runs/20260917T004356Z_s1_smoke/renders/scene_final.png`。

WebRTC：不適用。這一項應在終端確認；沒有可顯示該判定的模擬場景。

來源：本專案 PNG 統計檢查；非空白不代表語意／物理正確。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 08．五板件固定開口箱，中心 probe 落入箱內

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf box --case open_box_normal
```

成功條件：inside；正常案例 verdict=pass。

已保存證據：`runs/20260917T000053Z_s2_open_box_normal/s2_result.json`。

WebRTC：

```bash
./scripts/pf view --run 20260917T000053Z_s2_open_box_normal --scene scene_final.usda --ui
```

畫面確認：有底板＋四面牆且頂部開口，probe 在內底。

來源：本專案 handbook 第 7 節工程案例與 local-frame outcome；不是實測紙板箱。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 09．故障一：封口確實阻擋 probe

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf box --case open_box_sealed
```

成功條件：at_mouth；故障被偵測，所以測試 verdict=pass，資產本身不合格。

已保存證據：`runs/20260917T000106Z_s2_open_box_sealed/s2_result.json`。

WebRTC：

```bash
./scripts/pf view --run 20260917T000106Z_s2_open_box_sealed --scene scene_final.usda --ui
```

畫面確認：probe 停在封住箱口的板上，沒有進到箱底。

來源：本專案 handbook 第 7 節工程案例與 local-frame outcome；不是實測紙板箱。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 10．故障二：缺底確實讓 probe 掉落

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf box --case open_box_no_bottom
```

成功條件：fell_through；故障被偵測，所以測試 verdict=pass，資產本身不合格。

已保存證據：`runs/20260917T000039Z_s2_open_box_no_bottom/s2_result.json`。

WebRTC：

```bash
./scripts/pf view --run 20260917T000039Z_s2_open_box_no_bottom --scene scene_final.usda --ui
```

畫面確認：箱內沒有底板，probe 穿過箱體停在世界地板上。

來源：本專案 handbook 第 7 節工程案例與 local-frame outcome；不是實測紙板箱。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 11．尺寸變體：小箱仍能放置

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf box --case open_box_small
```

成功條件：inside、verdict=pass。

已保存證據：`runs/20260917T000122Z_s2_open_box_small/s2_result.json`。

WebRTC：

```bash
./scripts/pf view --run 20260917T000122Z_s2_open_box_small --scene scene_final.usda --ui
```

畫面確認：較小的箱體內有 probe，沒有停在箱口。

來源：本專案 handbook 第 7 節工程案例與 local-frame outcome；不是實測紙板箱。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 12．尺寸變體：高箱仍能放置

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf box --case open_box_tall
```

成功條件：inside、verdict=pass。

已保存證據：`runs/20260917T000150Z_s2_open_box_tall/s2_result.json`。

WebRTC：

```bash
./scripts/pf view --run 20260917T000150Z_s2_open_box_tall --scene scene_final.usda --ui
```

畫面確認：較高的開口箱，probe 在底部。

來源：本專案 handbook 第 7 節工程案例與 local-frame outcome；不是實測紙板箱。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 13．尺寸變體：厚壁箱仍能放置

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf box --case open_box_thick_wall
```

成功條件：inside、verdict=pass。

已保存證據：`runs/20260917T000211Z_s2_open_box_thick_wall/s2_result.json`。

WebRTC：

```bash
./scripts/pf view --run 20260917T000211Z_s2_open_box_thick_wall --scene scene_final.usda --ui
```

畫面確認：壁厚增加，probe 仍在較小內腔中。

來源：本專案 handbook 第 7 節工程案例與 local-frame outcome；不是實測紙板箱。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 14．連線後觀察 probe 開始落下

狀態：操作已實作；WebRTC hold/release 尚待人工驗證，不列為人已看過的成功。

重新執行：

```bash
./scripts/pf view --run 20260917T000053Z_s2_open_box_normal --scene asset.usda --hold-seconds 60 --ui
```

成功條件：這是供人工確認的操作，尚未有 WebRTC 人工成功紀錄；READY 後 60 秒解除 probe 的重力等待。

已保存證據：`runs/20260917T000053Z_s2_open_box_normal/asset.usda`。

WebRTC：

```bash
./scripts/pf view --run 20260917T000053Z_s2_open_box_normal --scene asset.usda --ui
```

畫面確認：先執行上方有 hold-seconds 的指令；連線後看到 probe 從上方開始掉落。新 viewer 的結果不是原驗收重播。

來源：本專案 viewer 的 hold/release 設計；本機 timeline PLAY 適配。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 15．三種時間步長的 containment 回歸

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf box --dt-sweep
```

成功條件：1/60、1/120、1/240 都 inside。不能據此宣稱 CCD 有效；目前 runtime 會警告停用 CCD。

已保存證據：`runs/20260916T141258Z_s2_open_box_normal_dt_sweep.md`。

WebRTC：

```bash
./scripts/pf view --run 20260917T000053Z_s2_open_box_normal --scene scene_final.usda --ui
```

畫面確認：最終 probe 在箱內；三組 dt 的比較看新的 suite，不是看這個固定場景。

來源：本專案案例與判定；方法依 docs/METHODS.md 及本機 Isaac Sim 6.0.1 API。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 16．幾何解析值與五板件位置

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
python3 -m unittest tests.test_geometry -v
./scripts/pf verify --case open_box_normal
```

成功條件：解析內腔 0.29×0.19×0.145 m、floor local z=0.005 m；G1 尺寸與 composed transform 讀回通過。解析精度不等於 USD 浮點精度。

已保存證據：`runs/20260916T163404Z_s3_verify_open_box_normal/validation.json`。

WebRTC：

```bash
./scripts/pf view --run 20260916T163404Z_s3_verify_open_box_normal --scene asset.usda --ui
```

畫面確認：選取五面板看 Properties 的尺寸與位置；精確誤差看 validation.json。

來源：本專案 handbook 第 7、19 節；OpenUSD composed transform，見 docs/METHODS.md。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 17．七類非法輸入在模擬前被拒絕

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
python3 -m unittest tests.test_schema -v
./scripts/pf verify --all
```

成功條件：7 個非法案例被 expected_error_class 拒絕；其餘合法案例通過。suite pass 代表拒絕正確，不代表非法輸入被接受。

已保存證據：`runs/20260916T163408Z_s3_verify_bad_wall_too_thick_suite.md`。

WebRTC：不適用。這一項應在終端確認；沒有可顯示該判定的模擬場景。

來源：本專案 schema／cross-field constraints；七例是專案測試集。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 18．官方 generic USD validator 41 rules 與負例自測

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf verify --case open_box_normal
python3 -m json.tool runs/20260916T163404Z_s3_verify_open_box_normal/validation.json
```

成功條件：官方 generic validator 通過，損壞 fixture 的 self-test 抓到失敗；不等於 SimReady 認證或箱內放置成功。

已保存證據：`runs/20260916T163404Z_s3_verify_open_box_normal/validation.json`。

WebRTC：

```bash
./scripts/pf view --run 20260916T163404Z_s3_verify_open_box_normal --scene asset.usda --ui
```

畫面確認：可以看箱體幾何；41 rules 與故意損壞 fixture 的檢出必須看 JSON。

來源：本機 omni.asset_validator 1.19.3；NVIDIA Asset Validation 來源見 docs/METHODS.md。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 19．USD 可 reference：defaultPrim 與可達 PhysicsScene

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
/mnt/HDD4/wyattsheu/IsaacLab/.venv/bin/python3 -m unittest tests.test_export_defaultprim -v
./scripts/pf verify --case open_box_normal
```

成功條件：本機 Isaac venv 執行 7 項 reference 測試全通過（不需啟動 Kit）；系統 Python 會 skipped，不算通過。G1.default_prim 亦應 pass。

已保存證據：`runs/20260916T163404Z_s3_verify_open_box_normal/validation.json`。

WebRTC：

```bash
./scripts/pf view --run 20260917T000053Z_s2_open_box_normal --scene scene_final.usda --ui
```

畫面確認：Stage tree 有 World、Box、Probe、PhysicsScene；現在 viewer 直接 open，畫面成功不等於 reference 測試成功。

來源：OpenUSD defaultPrim/reference 機制；本專案 exporter 適配。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 20．質量、COM、慣性解析計算

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
python3 -m unittest tests.test_mass_properties.TestHandbookSection19 -v
```

成功條件：殼體 mass=0.20 kg、COM z≈0.0552337952 m，Ixx/Iyy/Izz≈0.0016619320/0.0027588147/0.0034580587 kg m²；handbook 解析值吻合。

已保存證據：`runs/20260917T000047Z_s4_final_offline/unittest.log`。

WebRTC：

```bash
./scripts/pf view --run 20260916T163330Z_s4_dynamic_drop --scene scene_final.usda --ui
```

畫面確認：只能看動態剛體箱結構；解析值由終端驗證。

來源：handbook 第 19 節＋平行軸定理；均勻殼體模型與 mass 是估計。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 21．慣性可行性對旋轉與尺度不變

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
python3 -m unittest tests.test_mass_properties.TestPhysicalFeasibility -v
```

成功條件：旋轉後不可能的 tensor 被拒絕，小尺度合法 tensor 被接受；正定與主慣性矩三角不等式通過。

已保存證據：`runs/20260917T000047Z_s4_final_offline/unittest.log`。

WebRTC：不適用。這一項應在終端確認；沒有可顯示該判定的模擬場景。

來源：Scalable Real2Sim 的 physical feasibility 方法；來源見 docs/METHODS.md。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 22．動態箱 USD：一個 root body、五個 child collider

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf verify --case open_box_dynamic
```

成功條件：動態 USD 的 root MassAPI 與五面 collider 靜態檢查 pass。

已保存證據：`runs/20260916T155155Z_s3_verify_open_box_dynamic/validation.json`。

WebRTC：

```bash
./scripts/pf view --run 20260916T163330Z_s4_dynamic_drop --scene scene_final.usda --ui
```

畫面確認：在 Stage tree 選 World/Box 看 root 的 RigidBody／Mass；五面 child 有 collision，避免五個分離 body。

來源：本專案案例與判定；方法依 docs/METHODS.md 及本機 Isaac Sim 6.0.1 API。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 23．PhysX mass 讀回

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf mass-readback
python3 -m json.tool runs/20260916T155652Z_s4_mass_readback/s4_mass_readback.json
```

成功條件：mass absolute error 約 2.98e-9 kg；相應 S4.physx check=pass。只證明參數傳遞，不證明真實材料量測。

已保存證據：`runs/20260916T155652Z_s4_mass_readback/s4_mass_readback.json`。

WebRTC：

```bash
./scripts/pf view --run 20260916T163330Z_s4_dynamic_drop --scene scene_final.usda --ui
```

畫面確認：在 Properties 看 authored mass properties；內部 PhysX 精確讀回以 JSON 為準。

來源：OpenUSD MassAPI＋本機 PhysX tensor API；數值 tolerance 為專案 transport 判定。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 24．PhysX local COM 讀回

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf mass-readback
python3 -m json.tool runs/20260916T155652Z_s4_mass_readback/s4_mass_readback.json
```

成功條件：COM absolute error 約 4.49e-11 m；相應 S4.physx check=pass。只證明參數傳遞，不證明真實材料量測。

已保存證據：`runs/20260916T155652Z_s4_mass_readback/s4_mass_readback.json`。

WebRTC：

```bash
./scripts/pf view --run 20260916T163330Z_s4_dynamic_drop --scene scene_final.usda --ui
```

畫面確認：在 Properties 看 authored mass properties；內部 PhysX 精確讀回以 JSON 為準。

來源：OpenUSD MassAPI＋本機 PhysX tensor API；數值 tolerance 為專案 transport 判定。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 25．PhysX inertia 讀回

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf mass-readback
python3 -m json.tool runs/20260916T155652Z_s4_mass_readback/s4_mass_readback.json
```

成功條件：inertia absolute error 約 2.24e-11 kg m²；相應 S4.physx check=pass。只證明參數傳遞，不證明真實材料量測。

已保存證據：`runs/20260916T155652Z_s4_mass_readback/s4_mass_readback.json`。

WebRTC：

```bash
./scripts/pf view --run 20260916T163330Z_s4_dynamic_drop --scene scene_final.usda --ui
```

畫面確認：在 Properties 看 authored mass properties；內部 PhysX 精確讀回以 JSON 為準。

來源：OpenUSD MassAPI＋本機 PhysX tensor API；數值 tolerance 為專案 transport 判定。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 26．PhysX principal axes 讀回

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf mass-readback
python3 -m json.tool runs/20260916T155652Z_s4_mass_readback/s4_mass_readback.json
```

成功條件：principal axes quaternion absolute error 0；相應 S4.physx check=pass。只證明參數傳遞，不證明真實材料量測。

已保存證據：`runs/20260916T155652Z_s4_mass_readback/s4_mass_readback.json`。

WebRTC：

```bash
./scripts/pf view --run 20260916T163330Z_s4_dynamic_drop --scene scene_final.usda --ui
```

畫面確認：在 Properties 看 authored mass properties；內部 PhysX 精確讀回以 JSON 為準。

來源：OpenUSD MassAPI＋本機 PhysX tensor API；數值 tolerance 為專案 transport 判定。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 27．九點放置：中心、四邊與四角

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf placement-grid --physics-only
```

成功條件：9/9 inside，finite trajectory check=pass，render=not_tested。

已保存證據：`runs/20260917T000241Z_s4_placement_grid/s4_placement_grid.json`。

WebRTC：

```bash
./scripts/pf view --run 20260917T000241Z_s4_placement_grid --scene scene_final.usda --ui
```

畫面確認：九個分開的箱，每個 probe 在各自箱內；每點的最終 local xyz 看 summary.md。

來源：本專案案例與判定；方法依 docs/METHODS.md 及本機 Isaac Sim 6.0.1 API。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 28．四方向側撞：整段軌跡沒有越過牆

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
python3 -m unittest tests.test_sidewall -v
./scripts/pf sidewall --physics-only
```

成功條件：4/4 blocked；判定使用整段 trajectory 的最大越界值，而不只看最後位置。

已保存證據：`runs/20260916T163041Z_s4_sidewall/s4_sidewall.json`。

WebRTC：

```bash
./scripts/pf view --run 20260916T163041Z_s4_sidewall --scene scene_final.usda --ui
```

畫面確認：四個 probe 對應四個方向內牆；觀察最後位置不能證明整段軌跡沒有穿牆。

來源：本專案案例與判定；方法依 docs/METHODS.md 及本機 Isaac Sim 6.0.1 API。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 29．明寫 contact/rest offset 與物理材質 binding

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
python3 -m unittest tests.test_contact_settings -v
./scripts/pf sidewall --physics-only
```

成功條件：25 collider 綁定材料並讀回 contact offset=0.002 m、rest offset=0 m；material friction/restitution 在 JSON，且保持 estimated。

已保存證據：`runs/20260916T163041Z_s4_sidewall/s4_sidewall.json`。

WebRTC：

```bash
./scripts/pf view --run 20260916T163041Z_s4_sidewall --scene scene_final.usda --ui
```

畫面確認：選 collider 看 contact/rest offset 和 physics material binding；沒有宣稱讀到 PhysX 內部 coefficient getter。

來源：PhysxCollisionAPI／UsdPhysics.MaterialAPI；參數是專案工程 baseline。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 30．動態箱落地不分解、不穿地板

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf dynamic-drop
```

成功條件：one root body、five colliders；min root z≈-0.00425 m，within -0.005 m；final z≈1.49e-8 m。

已保存證據：`runs/20260916T163330Z_s4_dynamic_drop/s4_dynamic_drop.json`。

WebRTC：

```bash
./scripts/pf view --run 20260916T163330Z_s4_dynamic_drop --scene scene_final.usda --ui
```

畫面確認：完整開口箱停在地板上，五面沒有散開；這是最終場景，不是掉落動畫。

來源：本專案案例與判定；方法依 docs/METHODS.md 及本機 Isaac Sim 6.0.1 API。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 31．動態箱末段線速度與角速度穩定

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf dynamic-drop
python3 -m json.tool runs/20260916T163330Z_s4_dynamic_drop/s4_dynamic_drop.json
```

成功條件：末段 0.5 s max linear≈1.167e-5 m/s、angular≈6.456e-5 rad/s，settled checks pass。

已保存證據：`runs/20260916T163330Z_s4_dynamic_drop/trajectory.csv`。

WebRTC：

```bash
./scripts/pf view --run 20260916T163330Z_s4_dynamic_drop --scene scene_final.usda --ui
```

畫面確認：箱體保持穩定；精確速度和觀察窗口看 JSON，不以肉眼代替。

來源：本專案案例與判定；方法依 docs/METHODS.md 及本機 Isaac Sim 6.0.1 API。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 32．既有故障回歸與離線測試總驗收

歷史驗證：已保存成功證據；WebRTC 仍待你人工確認。

重新執行：

```bash
./scripts/pf verify --all
./scripts/pf box --all
python3 -m unittest discover -s tests -v
```

成功條件：靜態 13 案、物理 6 案均符合 expected；106 tests、7 skipped。跳過項不列為驗證成功。

已保存證據：`runs/20260917T000047Z_s4_final_offline/unittest.log`。

WebRTC：

```bash
./scripts/pf view --run 20260917T000053Z_s2_open_box_normal --scene scene_final.usda --ui
```

畫面確認：可分別回到本清單正常／封口／缺底場景確認差異；單一正常畫面不能證明整套回歸。

來源：本專案案例與判定；方法依 docs/METHODS.md 及本機 Isaac Sim 6.0.1 API。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 33．S5 修復合約格式：僅完成格式檢查

狀態：僅 JSON 語法／結構驗證成功；修復執行尚未實作。

重新執行：

```bash
python3 -m json.tool contracts/repair_proposal_v1.schema.json
cat docs/REPAIR_CONTRACT.md
```

成功條件：JSON 語法有效；attempt 上限 3、patch allowlist 明列。尚未有可執行 repair gate，不能宣稱限制已受執行層驗證。

已保存證據：`runs/20260917T000446Z_s5_contract_audit/result.json`。

WebRTC：不適用。這一項應在終端確認；沒有可顯示該判定的模擬場景。

來源：S5 task／handbook 第 11 節；critic 與 minimal patch 的研究來源見 docs/METHODS.md，欄位限制是專案設計。

我的確認：□ 未確認　□ 成功　□ 失敗；觀察／新 run-id：________


## 尚不能列為成功的項目

- WebRTC：所有場景仍待你人工連線確認；沒有自動宣稱人已看到。
- 新 S1 含 USD 的 render 嘗試 runs/20260917T004448Z_s1_smoke/ 崩潰，exit -11／pf 4。
  不能把舊 PNG 成功套到該次 run。S1 physics-only USD 證據另列於第 03 項。
- 側撞 offline renderer 曾崩潰；physics-only 不會產生 PNG。
- CCD 實際生效：runtime 警告 disabled；目前只保存 true attribute 和停用警告。
- 真實紙板／摺痕／flap 變形與材料校準：未完成。50 g probe 材料校準提案也不是驗證成功。
- intended_task 驅動檢查、S5 實際修復、S6／S7：未完成。

## 最省時間的順序

先看第 08、09、10 項的正常／封口／缺底三個場景，再看第 27–31 項的九點、
側撞、接觸與動態箱。之後從第 01 項起，逐項補上終端數值與你的確認紀錄。
參數傳遞、數學與負例測試不會多出一個可視動畫；它們是不同種類的成功點。

清單路徑與指令語法 audit：runs/20260917T004909Z_self_verification_audit/。
該 run 另保存 7 項 reference 測試與 106 項離線測試（7 skipped）的 exit 0 證據。

## S1 最終重跑更新

將最終 pose 的 USD 寫入安排在正常渲染之後，再跑預設 smoke 已通過：
runs/20260917T004937Z_s1_smoke/，runtime 與 pf exit 0；physics／readback／PNG pass。
1280×720、105571 bytes、98 個 red levels（統計非空白，未做人眼確認）。
此結果不改寫前一次失敗。

```bash
./scripts/pf view --run 20260917T004937Z_s1_smoke --scene scene_final.usda --ui
xdg-open runs/20260917T004937Z_s1_smoke/renders/scene_final.png
```
