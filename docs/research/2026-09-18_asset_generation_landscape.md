# 泛用物理資產生成：專案調查與採用建議

日期：2026-09-18（Asia/Taipei）。狀態：公開資料查證與設計建議，未安裝、下載模型、呼叫付費生成 API 或測試新後端。沒有宣稱已在本機 Isaac 6.0.1 通過。

## 結論

不存在本次證據足以支持的「所有物件一次生成、真實力學全部正確」業界最佳單一工具。
建議採用混合工作流：可替换的幾何／結構生成工具 + OpenUSD 資產契約 + 能力導向的物理行為配方 + 獨立驗收 + live 交付。
這是根據下列官方文件和研究提出的工程判斷，不是宣稱已有統一業界排名。
不枚舉所有商品：拆解部件、材料、接合及機器人動作。未知行為先做能力實驗，不能用已知物件名稱硬套。

## 原紀錄中的專案：哪些值得實際採用

原清單可追溯至 IsaacSim_Asset_Workflow_Handbook.md 第 54–60 行與 docs/METHODS.md；兩份新附件主要是實作事件。以下補充目前公開版本，與既有 pinned checkout 分開。

| 專案／一手來源 | 可取用的能力 | 在本案的位置與限制 | 建議 |
| --- | --- | --- | --- |
| [NVIDIA USD Content Agents](https://github.com/NVIDIA-Omniverse/usd-content-agents) | 內容工作流與工具、驗證／證據組織 | 保留已接的 adapter 和 pinned commit；不保證任意材料校準 | 保留主線 |
| [EmbodiedGen](https://github.com/HorizonRobotics/EmbodiedGen) | 文字／圖片生成資產，切換 SAM3D/TRELLIS/Hunyuan 後端，USD 轉換入口 | 優先接單物件輸出，不導入房間、訓練和所有服務；物理值包含 VLM 推估，必須標來源 | 首個外部候選 |
| [Articulate-Anything](https://github.com/vlongle/articulate-anything) | 文字／圖片／影片推斷可動部件、程式化 articulation、actor–critic | 適合蓋子、抽屜、鉸鏈的結構提案；不是紙板塑性或膠帶剝離定律 | 借方法；可動資產第二階段 |
| [LL3M](https://github.com/threedle/ll3m) | 以 Python 建立可修改的 Blender 資產 | 借文件檢索＋程式建模；外觀品質不等於碰撞／物理正確，README 提到論文原模型已退役 | 融入現有建模路徑，先不重建全套 |
| [Scalable Real2Sim](https://arxiv.org/abs/2503.00370) | 結合觀測與機器人互動辨識物件幾何／慣性 | 有實物時作辨識方法參考；不是從單張照片知道內部質量分布 | 校準路徑 |
| [Kit USD Agents](https://github.com/NVIDIA-Omniverse/kit-usd-agents) | USD／Kit 開發與工具協調基礎 | 不填補物理參數真值；目前已有直接工具，不必為使用它新增 MCP | 暫緩基礎設施整合 |

EmbodiedGen 目前 README 的版本路徑是 v2.1.0；列出 MeshtoUSDConverter，輸出也包含 URDF／mesh。它的柔性服裝範例部署在 Genesis，不能據此宣稱 Isaac 的柔性包材可直接用。repo 標示 Apache-2.0；後端模型、權重和素材依賴須各自檢查。

## 新增候選：圖片到 3D、部件與物理

| 專案／來源 | 能力及可用性 | 我們應如何使用 |
| --- | --- | --- |
| [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | 圖片到有材質的 3D mesh；公開推論與權重，code/model 標示 MIT，部分依賴另有條款 | 複雜外觀候選；輸出再做尺度、部件、碰撞及物理處理。官方說至少 24 GB GPU 且驗過 A100/H100，本機效能仍未知 |
| [SAM 3D Objects](https://github.com/facebookresearch/sam-3d-objects) | 從圖片重建物體形狀、外觀與配置；code/checkpoint 採 SAM License | 適合場景中選取目標作重建；不假設看不到的內腔／接縫正確。作圖片後端比較候選 |
| [Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) | 圖片幾何與 PBR 材質生成；[權重授權](https://huggingface.co/tencent/Hunyuan3D-2.1/blob/main/LICENSE)為自訂 Community License | 備選外觀後端；PBR 是光學材質，不是摩擦、屈服或彈性模數 |
| [PartCrafter](https://github.com/wgsxm/PartCrafter) | 單圖生成多個具語義部件的 mesh；有 inference/checkpoint；[程式 MIT](https://github.com/wgsxm/PartCrafter/blob/main/LICENSE) | 避免所有零件黏成一塊的候選；部件分開後仍需確認接合拓撲、關節和碰撞 |
| [PhysX-Anything](https://github.com/ziangcao0312/PhysX-Anything) | 圖片生成幾何、關節與物理属性；有官方研究程式 | 比純外觀更接近需求；推斷參數仍不能視為實測；Isaac 匯入與被動性需另驗 |
| [PhysX-Omni](https://github.com/physx-omni/PhysX-Omni) | 研究擴至剛體、柔性和可動物件；README 有權重入口、URDF/XML 輸出、PhysX-Bench | 研究對照候選；不是直接交付完整 Isaac USD 的保證，也不是 NVIDIA 官方 PhysX 功能 |
| [PhysTwin](https://github.com/Jianghanxiao/PhysTwin) | 從 RGB-D 互動影片重建柔性物體的物理模型 | 對已存在的包材做實測導向辨識；需要資料採集，不是文字生成器，也不能假設自動轉成等效 PhysX 材料 |
| [DeformSmith 論文](https://arxiv.org/abs/2609.18620) | 2026-09-16 新預印本，以分層生成和物理測試協同建立柔性資產 | 研究方向很接近需求；本次作者專案頁載入失敗，程式／權重／授權未確認。只列追蹤，不列可部署方案 |

[PhysX-Omni 的 S-Lab License](https://github.com/physx-omni/PhysX-Omni/blob/main/LICENSE)明列非商業用途條件，商用需聯絡作者。公司用途採用前須確認授權，不能因 repo 公開就算可自由交付。
其餘未逐一核對所有相依套件／資料／權重的授權，狀態是待審核，不做法律合規結論。

## 為何圖片生成 3D 可以用，但不能單獨完成任務

照片提供可見表面和外觀線索，隱藏內部、絕對尺度、厚度、摩擦對、張力、損傷、黏著與質量分布通常不能唯一決定。
預設取得至少一個可靠尺寸；有內腔、薄邊或遮蔽的工作區域時，補多視角、CAD 或掃描，否則標記幾何假設。
反光／透明泡泡紙尤其不能只看重建表面就聲稱機械結構已正確。

輸入文字／圖片／影片／CAD
→ 辨識任務與部件／界面
→ 優先搜尋合適的已有資產；規則結構走參數化建模，複雜外觀走 image-to-3D，多視角資料走重建
→ 視覺 mesh、碰撞 proxy、物理拓撲分開處理
→ 尺度、質量、材料、接合、內部狀態與 runtime
→ 在現有 Isaac 中作靜態＋任務／材料＋數值測試
→ USD＋必要 runtime＋WebRTC 操作卡。

例如「紙箱包著泡泡紙馬克杯」不是單一 mesh，而是包裝層級：箱體、四蓋、膠帶、膜、杯子，及其接觸／接合。
杯子外觀可生成；杯口和把手必須有可用碰撞幾何。箱蓋以可編輯板片與摺痕構造。膜須有邊界、重疊、接合與可釋放路徑。
抓整個包裹只需較低精度代理；拆包需要可分離層與接合；壓破則需另加經驗證的損傷能力。依任務選最低足夠複雜度。
不要把生成包好的外表殼當成已能拆包。裝配／包裹工序本身會決定預張力、初始應力與接觸。

## 可以泛化的核心：物理行為與接合圖

建立可擴充能力字彙而不是商品清單：剛體、旋轉／平移接合、膜／殼彎曲、體積壓縮、摩擦、黏著／剝離、塑性、損傷等。
這不是宣稱列舉完所有物理；遇到未知或後端不支援的機制，明確列 capability gap，安排最小實驗或提高輸入要求。
每個部件與界面對應行為配方和驗收，組裝後再驗交互作用，不能只測單一元件。
AI 可以提名所需能力和測試，已審核的契約與驗證器才決定必測項；生成器不能自行刪掉失敗的檢查。

只問對任務結果最敏感且資料不足的問題。來源明確的預設可重用；質量／尺度／材料未知且重要時，要求量測或提供帶來源的範圍。
沒有實物也可以做探索，但交付是「假設下的模擬」，不能叫特定實物的可信數位分身。

## 最佳實務依據及版本界線

[NVIDIA SimReady FAQ](https://docs.omniverse.nvidia.com/simready/latest/simready-faq.html)把靜態結構／metadata 驗證和真正 runtime 行為測試分開；也指出組合場景仍需在目標模擬器執行。
因此本案採「通用標準＋任務專用測試」有官方依據，不能只增加 Asset Validator rule 數量。
網頁目前的 SimReady Foundation／Isaac 6.1 文件不代表本機 6.0.1 已具备其全部套件，不能直接照 latest API 改主線。
不把跨模擬器格式轉換等同物理行為等價；關節單位、摩擦、碰撞、deformable 和 callback 都要在目標後端重新量測。

## 建議的採用順序與小規模評測

1. **先加通用輸入契約與能力圖。** 接受 text/image/CAD/已有 mesh，保存 metric scale、部件、接合、參數來源、generator/version、必測能力和 runtime requirements。不新建大型平台。
2. **第一個外部 adapter 選 EmbodiedGen 單物件路徑做資格測試。** 先用其已整合的其中一個圖片後端，不假定已支援 TRELLIS.2；若另加 TRELLIS.2，作獨立 adapter 驗證。
3. **保留參數化建模作對照。** 紙箱這類尺寸／厚度／接合主導的資產不必為了用 AI 圖片模型而改成不可編輯 mesh。
4. **再接可動部件路徑。** 先測 Articulate-Anything 方法或部件生成，檢查自由度和受力反應，不直接使用動畫作通過證據。
5. **柔性和黏著單獨做研究能力卡。** 參考 PhysTwin、PhysX-Omni／DeformSmith 思路；授權和目標 runtime 能力先確認。

初始評測用四種不同機制，而不是四個外觀不同的紙箱：
- 不規則剛性物件：看 image-to-3D 尺度、碰撞、質量與抓取接觸。
- 有獨立蓋的容器：看部件、關節、接觸阻擋與被動開合。
- 柔性包裝＋硬內物：看層間接觸、可壓縮／彎曲能力和解包；未支援列缺口。
- 未參與開發的保留物件：檢查能否重用行為配方，未知能力能否正確拒絕。

每個路徑用相同需求／來源／尺度資訊及修復預算，保留所有失敗；能控制時固定 provider/model/seed，不能控制時明列差異。
至少多次生成後分報：幾何首輪成功、必要能力覆蓋、任務成功、錯誤通過、人工補問／修改次數、牆鐘時間、成本、VRAM、冷載入／WebRTC。
不引用論文某顆 GPU 的秒數宣稱本機一樣快；生成圖像的審美品質不作機器人可操作性的替代指标。

## 執行環境與交付

新生成器未來放隔離的環境或容器，檔案交接，不安裝進 Isaac 共用 venv；本次完全未安裝。
GPU 每次實跑前檢查資源，排隊或 blocked，不停止其他使用者程序。官方 API／權重可用性在接入前再做 capability probe。
交付保留被動物件與必要材料 runtime，讀回 mass、collision、joint、material，以及 reset／history semantics。
每次附真正在既有 WebRTC 入口測過的載入指令與兩三個小操作，沒有人工確認前寫 human_webrtc=not_tested。
影片僅里程碑背景錄製；工作流建置報告與個案運行進度沿用不同 reports 資料夾。

下一個有界工作：P0 加入通用輸入契約／能力圖，並建立 EmbodiedGen 單物件 adapter 的資格測試卡；未來先驗一件剛性物件，不一次整合所有框架。
