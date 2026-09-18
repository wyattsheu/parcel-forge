# 可開合紙箱與鍵盤比較：範圍與驗收計畫

目前完成的是本地 primitive rigid box → USD → PhysX → task gate → 官方 focused
驗收與受限 fault 修復執行。歷史證據 20260917T075134Z_s5d_repair_execution。
模型／外部幾何生成、通用 task dispatch、批次 sealed test、冷啟動交付、紙箱力學皆未完成。
使用者確認 3D 看起來正常是 human visual feedback，不是材料驗證。
舊約 70% 只適用原 primitive S0–S7 階段估計；加入紙箱與鍵盤比較後不沿用該百分比。
本次為評估與文件更新，未重跑物理或宣告最新環境重驗通過。

## 紙箱：先建可測的折痕，再擴展四片蓋

目標先設為底部封好的瓦楞 RSC 箱體＋四片上蓋；底部四片活動蓋另列後續。
理想零厚度 RSC flap nominal length=W/2；實際厚度、槽口、折線偏移與閉合間隙
需獨立規格，不能只以中心零間隙證明閉合可用。

1. 單蓋幾何／鉸鏈：固定箱壁＋一片剛體蓋＋revolute joint。記錄軸、角度符號、
限位、質量／慣量、角速度；角度零點明確定义。用已安裝 Isaac API 實測施力與讀回。
2. 彈性模型：torsional spring/damper，M=k(theta-theta0)+c*theta_dot。
以分離的力矩控制施載，不能用位置 drive 強制達標再當物性驗證。檢查
正／負力矩反應、小負載回復、重力平衡、阻尼與 dt 收斂。
3. 非線性歷史模型：增加塑性休止角／載入卸載狀態，先用可檢查的 elastic-plastic
模型，再依量測決定是否需要 softening、峰值或回線查表。門檻判斷看材料阻力矩，
不可將包含慣性、限位或接觸的 total joint reaction 直接視為材料屈服。
每步更新一次狀態；驗證耗散、殘餘角、重複循環及步長收斂，避免每步重複乘軟化係數。
4. 四蓋交互：內蓋／外蓋依序開關，檢查互撞、限位、閉合重疊與穿透；全開時沿用
放置任務。膠帶／鎖扣破壞力要另外建模，不能混作折痕屈服。
5. 實物校正：固定牆面，在已知作用點以測力計低速往返折疊，量角、力、方向、力臂。
M=|r×F|，只有垂直施力才簡化為 F*l；扣除蓋重力矩、治具摩擦。
同批至少 5 個樣本作 pilot，記厚度、楞向、濕度、折痕加工與循環次數；
量測低／高幅度載入卸載及多次循環，用不同樣本保留驗證，不拿同一曲線同時擬合與驗收。

驗收指標：M(theta) 曲線誤差、峰值力矩、卸載斜率、零載殘餘角、回線耗散面積、
第 1/2/5 次循環差異、接觸穿透與能量穩定性。誤差門檻在測試前根據儀器不確定度與
任務需求固定；沒有實物數據前 provenance=uncalibrated_assumption。
小負載也可能造成彈性變形；不是「超過一個力才開始動」。預壓折痕不一定有明顯屈服峰。
剛體蓋＋等效折痕可研究開蓋力；不能證明板面彎曲、壓潰、撕裂或防撞緩衝真實。

## 鍵盤：先共同規格，再比效率

NVIDIA README 展示 generated keyboard 的 robot-learning polish 圖；公開圖不足以
取得相同 prompt、provider、硬體、模型與總工時。benchmark 文件明說執行框架與多個
標準資料集屬內部 QA，因此目前只能做「依官方方法的公開可重現比較」，不能宣稱復現其速度。

先用兩個獨立難度，不能把靜態外觀和機器人打字训练混成一次生成效率：
- K1 靜態鍵盤：固定尺寸、鍵數、鍵距、外殼、獨立鍵帽及語意命名、材質、可打開 USD。
- K2 可按壓鍵盤：增加各鍵獨立 prismatic joint、指定行程／力—位移回復曲線、
按下一鍵不帶動鄰鍵、接觸／重複按壓／數值穩定。機器人策略训练另計，不是必需前置。

比較組 A：固定上游版本＋官方 agentic/provider 路徑。
比較組 B：同 provider／模型／prompt／硬體＋本地 workflow adapter。
目前本地 schema/generator 只支援箱子，B 組需先實作鍵盤／task dispatch，不能直接套
box containment 驗收；未完成前先量 A 組基線，不做錯誤 A/B 宣稱。
手工 primitive 鍵盤可作驗收 oracle／成本參考，不能冒充文字生成結果。

每組至少 5 次 fresh-run pilot、固定成功 gate/重試上限/超時，交错執行。
分開記冷啟動安裝與 warm-run；保留失敗、timeout、拒絕與重試，不能只算成功案例。
記端到端 wall time、provider wait、生成／轉換／驗證／render 用時、人工介入分鐘、
工具／模型版本、token/API cost（不可得就 unknown）、GPU peak、成功率與品質。
報 median、range；5 次不宣稱穩健 p95 或統計顯著優勢。比較 time-to-accepted-asset，
只有兩組相同品質門檻都能完成時才談效率。圖像/影片只是證據，不取代關節/接觸量測。

資料分為 development/validation/sealed test，按資產家族切分，已看過的官方鍵盤
只能作 development benchmark。目前 fault fixture 明示 geometry.fault、甚至 expected_outcome，
可測控制器邊界，不能當盲測模型診斷能力。模型輸入排除 oracle 故障標籤，私有 evaluator
仍保留完整原始 spec／expected outcome 與 hash，不能改舊證據。

## 與官方相似程度與順序

相似／已用：模組分工、固定來源版本、可追蹤 run 證據、獨立 validation；
官方 focused prepare/check/finalize 已實際調用。
本地特有：固定 probe/profile 的 placement gate、三次提案預算、source hash chain。
未完整重現：自然語言→外部 authoring provider、Material/Joint 完整流程、官方 OVRTX
出圖、鍵盤 benchmark、sealed test、模型成本／效率比較。geometry dry-run 只證明規劃入口。

優先順序：P0 凍結範圍與量測標準 → P1 單折痕可動 USD 與 force/angle CSV →
P2 校正折痕及四蓋開合 → P3 官方鍵盤 K1 生成基線 → P4 K2 關節與公平 A/B。
模型/provider 可用性盤點可在 P1 前做 read-only；不要因無 endpoint 停住紙箱建置。
每次一張 bounded task；S5-D 保留未完成狀態，下一個實作卡改 EXT1 Stage A/B 的單蓋最小實驗。

## 來源

- NVIDIA README: https://github.com/NVIDIA-Omniverse/usd-content-agents/blob/a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa/README.md
- NVIDIA benchmark 方法／內部資料限制: https://github.com/NVIDIA-Omniverse/usd-content-agents/blob/a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa/agentic/docs/benchmarks.md
- Beex & Peerlings (2009), laminated paperboard creasing/folding, experimental moment-angle validation: https://publications.uni.lu/bitstream/10993/17431/1/BeexPeerlings2009.pdf
- Large bending behavior of creased paperboard I (2013), crease depth/large-angle response: https://www.sciencedirect.com/science/article/pii/S0020768313002217
- Repeated folding moment/hysteresis/residual angles (2011): https://www.jstage.jst.go.jp/article/jamdsm/5/4/5_4_385/_article

上述 paperboard 研究提供方法依據，不能直接移植其材料常數到我們的瓦楞紙箱。
既有研究文檔的 deformable 限制引自舊 IsaacLab 討論，不作為已安裝 Isaac 6 的已驗證限制。
本次未判定 FEM 可用或不可用；如剛體蓋不足以滿足板面變形需求，再作版本匹配可行性實測。
