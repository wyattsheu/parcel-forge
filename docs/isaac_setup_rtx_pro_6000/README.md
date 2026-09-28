# Isaac Sim / Isaac Lab 安裝手冊 — RTX PRO 6000 Blackwell（acm-803-1）

> 給新加入的人照著做的環境建置文件。這份是「活文件」：每次建環境、踩到新的坑就回來更新。
> 最後更新：2026-09-28（在學生容器 `student01-dev` 內實測）

## 0. 標記說明

每個結論都標註可信度，避免把猜測當事實：

- **[已驗證]**：在這台機器上實際跑過、看到結果。
- **[推論]**：依官方文件或現象推得，沒有單獨驗證。
- **[未驗證]**：記錄下來備查，沒有重跑確認。

**目前最大的缺口**：現有環境是「既有安裝」，這份文件的安裝步驟是依官方文件與現況重建的，
**尚未在乾淨環境從零完整重跑一次**（約需下載 27GB，未執行）。第一個照著做的人請把卡住的地方
補回「踩坑清單」。

## 1. 這台機器與已驗證的版本組合

| 項目 | 值 |
|---|---|
| 主機 | `acm-803-1`，Ubuntu 24.04.3，kernel 6.14 |
| GPU | 2 × NVIDIA RTX PRO 6000 Blackwell Max-Q（各 ~95 GiB，`sm_120`） |
| Driver / CUDA | 580.126.09 / CUDA 13.0 |
| Docker | 28.5.1，**rootless**（帳號不在 `docker` 群組，不可用系統 rootful daemon） |
| NVIDIA Container Toolkit | 1.18.0 |

**學生容器內的實測組合（[已驗證]，2026-09-28）：**

| 項目 | 值 |
|---|---|
| Base image | `nvidia/cuda:12.6.3-devel-ubuntu24.04` |
| Python | 3.12.14（由 `uv` 管理，`~/.local/share/uv/python/`）；專案要求 `>=3.12,<3.13` |
| Isaac Sim | 6.1.0.0（`isaacsim[all,extscache]`，pip 套件，非獨立安裝檔） |
| Isaac Lab | `develop` 分支，commit `e3521042a`（2026-09-26），套件版本 29.1.0 |
| PyTorch | 2.12.0+cu130（來自 `download.pytorch.org/whl/cu130`） |
| warp | 1.17.0，看得到 `cuda:0 ... (95 GiB, sm_120)` |
| uv | 0.12.19 |

**對照：主機原生環境（[已驗證]，2026-09-28）** 有兩個 venv，都是較舊的組合，且彼此也不同：

| venv | isaacsim | isaaclab | torch | Python 來源 |
|---|---|---|---|---|
| `~/IsaacLab/.venv`（實際在跑的，`isaaclab-dev`） | 6.0.1.0 | 16.4.0 | 2.11.0+cu128 | uv 下載的 3.12（`~/.local/share/uv/python/`） |
| `~/env_isaaclab` | 6.0.0.0 | 16.4.0 | 2.11.0+cu128 | 系統 `/usr/bin` Python 3.12.3 |

主機的 `~/IsaacLab` 停在 feature 分支（`feat/task1-rigid-asset-pipeline`，基於 2026-09-08 的 develop）。
**學生容器（Isaac Sim 6.1.0 / torch cu130）與主機（6.0.1 / cu128）版本不同，不要假設腳本兩邊通用。**

> Isaac Lab 追蹤的是 `develop`，更新很快。建議之後把 commit 固定下來（見踩坑 #10）。

## 2. 路徑 A：在 Docker 容器內安裝（學生環境）

### 2.1 容器啟動參數的硬性需求

完整範例見 `~/student_env/student01/run-container.sh`。與 Isaac Sim 直接相關的：

- `--gpus '"device=<GPU UUID>"'`：用 UUID 綁定，不用 index。
- `-e NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics`：**必須含 `graphics`**，
  否則沒有 Vulkan/EGL 用的驅動函式庫。[已驗證]
- `--shm-size 8g`（或更大）：PyTorch / Kit 會用到共享記憶體。[推論：本次未測試較小值]
- 容器內看到的 GPU 編號永遠是 `0`（`cuda:0`、Vulkan `GPU0`），即使它在主機上是 GPU 1。[已驗證]

### 2.2 映像必須內建的東西（`build/Dockerfile.student`）

**(a) 系統套件**（[已驗證] 已安裝並可運作；其中 `libxrandr2 libxinerama1 libxcursor1 libxi6
libfontconfig1 libnss3` 是依 Omniverse Kit 常見相依「預防性加入」，**未逐一證明缺少就會失敗**）：

```
libvulkan1 libegl1 libgl1 libglvnd0 libxext6 libxt6 vulkan-tools
libxrandr2 libxinerama1 libxcursor1 libxi6 libfontconfig1 libsm6 libice6 libnss3
```

**(b) NVIDIA Vulkan ICD 與 EGL vendor 設定檔（rootless Docker 特有的坑）**

這台主機的 rootless Docker 下，`NVIDIA_DRIVER_CAPABILITIES=graphics` 只會把 NVIDIA 驅動的 `.so`
掛進容器，**不會**自動產生指向它們的 ICD json，Vulkan loader 找不到驅動，Kit 渲染器初始化失敗。
需要在映像內手動建立：

`/usr/share/vulkan/icd.d/nvidia_icd.json`
```json
{ "file_format_version" : "1.0.1",
  "ICD": { "library_path": "libGLX_nvidia.so.0", "api_version" : "1.4.312" } }
```
`/usr/share/glvnd/egl_vendor.d/10_nvidia.json`
```json
{ "file_format_version" : "1.0.0",
  "ICD" : { "library_path" : "libEGL_nvidia.so.0" } }
```

驗證（[已驗證]）：容器內 `vulkaninfo --summary` 應看到
`deviceName = NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition`、`driverInfo = 580.126.09`。

### 2.3 安裝 Isaac Lab（在容器內、用一般使用者）

> 以下步驟 **[推論]**：依官方 `docs/source/setup/installation` 的 uv 流程與現況重建；
> 當初實際輸入的指令沒有留存（見 §6.1）。沒有 root 時的取捨與其他方法見 §6。

```bash
# 1) 安裝 uv（安裝後會產生 ~/.local/bin/env）
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# 2) 取得 Isaac Lab（放在持久化的 /workspace，不要放 image 內）
cd /workspace
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab

# 3) 第一次執行時 uv 會自動建立 .venv、下載 Python 3.12、安裝核心相依。
#    要 Isaac Sim 本體需帶 --extra isaacsim（官方文件寫法）：
uv run --extra isaacsim python scripts/tutorials/00_sim/launch_app.py
```

第一次會下載大量套件；完成後 `.venv` 約 **27GB**、`~/.cache/uv` 另約 **27GB**（見踩坑 #8）。
之後 `uv run python ...` 不必再帶 `--extra`（[已驗證]：現有環境用不帶 extra 的 `uv run` 可直接啟動）。

### 2.4 驗證

```bash
cd /workspace/IsaacLab
source $HOME/.local/bin/env
OMNI_KIT_ACCEPT_EULA=YES uv run python scripts/tutorials/00_sim/launch_app.py
```

**成功的樣子（[已驗證]，2026-09-28）：**
- 出現 `"cuda:0" : "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition" (95 GiB, sm_120 ...)`
- 出現 `[INFO]: Setup complete...`
- 之後不會自己結束（腳本是 `while simulation_app.is_running()` 迴圈），用 `Ctrl+C` 結束。
  在自動化測試中用 `timeout N` 砍掉時，未留下殘留 process。

## 3. 踩坑清單

| # | 症狀 | 原因 | 解法 | 狀態 |
|---|---|---|---|---|
| 1 | Kit 起不來、Vulkan/渲染器初始化失敗 | rootless Docker 不會產生 NVIDIA Vulkan ICD / EGL vendor json | 映像內手動建立兩個 json（§2.2b） | 已驗證 |
| 2 | 容器內沒有 Vulkan/EGL 驅動函式庫 | `NVIDIA_DRIVER_CAPABILITIES` 少了 `graphics` | 設 `compute,utility,graphics` | 已驗證 |
| 3 | 啟動時卡在 `Do you accept the EULA? (Yes/No)`；非互動執行則報 `Unable to bootstrap inner kit kernel: EULA not accepted` | Omniverse Kit 授權同意 | 互動環境輸入 `Yes`，或**閱讀授權後**設 `OMNI_KIT_ACCEPT_EULA=YES`。**授權同意由使用者本人決定，建置者不要代為永久寫進 `.bashrc`** | 已驗證 |
| 4 | log 出現 `failed to open the default display. Can't verify X Server version` | 容器內沒有 X display | 無害，可忽略（仍出現 `Setup complete`） | 已驗證 |
| 5 | 學生缺系統套件卻無法自行安裝 | 預設 `no-new-privileges` + 無 sudoers 條目，`sudo` 失效 | 本環境由擁有者決定給 `NOPASSWD` sudo 並移除 `no-new-privileges`（安全取捨見 `~/student_env/student01/OPERATIONS.md`） | 已驗證 |
| 6 | Blackwell（`sm_120`）上 PyTorch 找不到可用 kernel | 舊 CUDA 版 PyTorch 不含 `sm_120` | 使用專案指定的 `torch 2.12.0+cu130`（pyproject 已設 `pytorch-cu130` index），不要自行換成 cu12x 版 | 已驗證（目前組合可運作）；舊版失敗為推論 |
| 7 | 容器內 `nvidia-smi` 顯示 GPU 0，但主機上是 GPU 1 | 容器只看得到被分配的那一張，重新編號 | 正常現象；以 UUID 對應 | 已驗證 |
| 8 | 磁碟用量 ~54GB（`.venv` 27G + `~/.cache/uv` 27G） | venv 在 bind mount（`/workspace`）、uv cache 在 named volume，跨掛載點無法 hardlink，等於存兩份 | 預留 ≥ 60GB。若要省空間，可考慮把 cache 與 venv 放同一掛載點 | 用量已驗證；原因為推論 |
| 9 | `docker run <映像> <指令>` 指令沒被執行、容器卻一直掛著 | 映像的 `ENTRYPOINT` 會啟動 sshd/code-server，額外參數被忽略 | 除錯時用 `--entrypoint sh` 覆寫 | 已驗證 |
| 10 | `git pull` 時 `uv.lock` 有衝突 | `uv run` 會改寫 `uv.lock`（本次只是把內部套件版本號更新，如 `isaaclab 29.0.0 → 29.1.0`） | pull 前先 `git checkout uv.lock`（或 stash）；要可重現請固定 commit：`git checkout e3521042a` | 現象已驗證；衝突情境為推論 |
| 11 | 共用 GPU 上顯存不足 / 被搶 | Docker `--memory` 管不到 VRAM；兩張卡常被其他工作佔滿 | 開跑前 `nvidia-smi` 看剩餘顯存；不要假設獨佔 | 已驗證（觀察到 GPU 已被大量佔用） |

## 4. 資源與容量

- 磁碟：見踩坑 #8，單一學生環境約 54GB（本機 `/mnt/HDD4` 尚有 ~11TB）。
- GPU 顯存是**共用**的：建置當下 GPU 1 已被其他工作佔用 ~73GB / 97GB。
- 容器資源限制（本環境）：8 CPU、32GB RAM、8GB shm、PID 上限 4096。

## 5. 已知不支援：容器內 WebRTC 即時串流

學生容器目前**無法**做 Isaac Sim WebRTC livestream。原因：WebRTC 影像走 UDP、需要直接可達的
port，不能包進現有的受限 SSH tunnel；開公網 UDP 違反本環境「只綁 127.0.0.1」的設計；走 Tailscale
需要 tailnet 管理者邀請裝置，該權限不在這個帳號上。替代方案：把結果輸出成影片/截圖存到 `/workspace`。
（決策脈絡見 `~/student_env/student01/OPERATIONS.md`。）

## 6. 沒有 root / sudo 的情況：這台機器實際怎麼裝，以及其他方法

這台機器的使用者帳號**沒有 root、沒有 sudo、也不在 `docker` 群組**。所有安裝都必須在自己的 home 內完成。

### 6.1 這台機器上原生（主機）安裝的做法 —— 用 `uv`

**證據（[已驗證]）**：兩個 venv 的 `pyvenv.cfg` 都帶 `uv = 0.12.11`；`uv` 位於 `~/.local/bin/uv`；
`IsaacLab/.venv` 的 Python 位於 `~/.local/share/uv/python/`（uv 自己下載的，免 root）；
`env_isaaclab` 則是用系統既有的 `/usr/bin` Python 3.12.3。
**推論**：`env_isaaclab` 是照官方文件的 `uv venv --python 3.12 --seed env_isaaclab` 建的
（`seed = true` 吻合）；`IsaacLab/.venv` 是 `uv sync/run` 在專案內建的。
**未能還原**：當初實際輸入的完整指令沒有留存（`~/.bash_history` 內沒有任何 `uv`/isaac 安裝紀錄），
所以 §2.3 的步驟是「依官方文件重建」，不是逐字重現。

### 6.2 為什麼一定要用 `uv`（[已驗證] 的限制）

- 系統 Python 3.12.3 **缺 `ensurepip`**（`python3 -c "import ensurepip"` 失敗；要裝 `python3-venv` 才有，那需要 root）。
  所以標準的 `python3 -m venv` 在這台機器上**無法**直接用。
- `uv venv` / `uv sync` 不依賴系統的 `python3-venv`，且能自己下載 Python，因此免 root 可行（推論其機制；結果已由現有 venv 證明可行）。

### 6.3 哪些東西「需要 root」、目前由誰提供

| 需求 | 需要 root？ | 這台機器現況 |
|---|---|---|
| GPU 驅動（580.x） | 是 | 管理者已裝 |
| Vulkan / X11 執行期函式庫（`libvulkan1`、`libXrandr` 等） | 是（apt） | **主機上已全部存在**（[已驗證]），所以原生免額外處理；容器映像則必須自己內建（§2.2） |
| NVIDIA Container Toolkit | 是 | 管理者已裝 |
| `docker` 群組權限 | 是 | **沒有** → 改用 rootless Docker（見下表 B） |
| `python3-venv` | 是 | 沒有 → 用 `uv` 繞過 |
| `uv`、Python、Isaac Sim/Lab（pip 套件）、PyTorch | **否** | 全部裝在 `$HOME` |
| `loginctl enable-linger`（讓 rootless daemon 常駐） | 否（本機實測可自行執行） | 已啟用 |

### 6.4 其他免 root 的方法（比較）

| 代號 | 方法 | 免 root？ | 在這台機器上的狀態 | 適用情境 / 備註 |
|---|---|---|---|---|
| **A** | **`uv` + pip wheel**（`uv run --extra isaacsim`） | 是 | **已驗證**（主機兩個 venv + 學生容器） | 首選。可重現（有 `uv.lock`）。主機需已有 Vulkan/X11 函式庫 |
| **B** | **rootless Docker + 容器內 `uv`** | 是（需 `uidmap`、`/etc/subuid` 範圍、user namespace；本機皆具備） | **已驗證**（學生環境） | 需要隔離、或主機缺系統函式庫時。要自行處理 Vulkan ICD json（§2.2b） |
| C | `micromamba`/conda 環境 + `pip install isaacsim` | 是 | **未驗證**（`~/micromamba` 只有執行檔，沒有建過任何 env） | 想用 conda 生態時。Isaac Sim 仍是 pip 套件，conda 只負責 Python；缺系統函式庫時，可能可用 conda-forge 補（**未驗證**） |
| D | Isaac Sim 官方 standalone 壓縮包（解壓到 home） | 通常是 | **未驗證**（未確認 6.x 是否仍提供、體積、授權下載流程） | 需要完整 Kit 應用、不想用 pip 時 |
| E | NVIDIA NGC 官方 `isaac-sim` 映像 | 視 Docker 而定 | **未驗證**（需 NGC 帳號登入；rootless 下 GPU/Vulkan 行為未測） | 想少維護 Dockerfile 時；預期同樣要處理 rootless 的 Vulkan ICD 問題（推論） |
| F | rootful Docker（`docker` 群組） | 需管理者加群組 | **不可用**（帳號不在群組） | 若管理者日後加入群組則可行，但安全面比 B 差（容器 root 即主機 root 風險） |
| ✗ | 系統 `python3 -m venv` + `pip` | — | **失敗**（缺 `ensurepip`） | 不要走這條 |

**建議順序**：先用 A；需要隔離或分給他人用就用 B；C/D/E 只有在 A/B 都不適用時才試，並把結果補回這張表。

## 附錄 A：主機原生環境的 WebRTC 修法索引（[未驗證]，2026-09-10 的調查紀錄）

主機原生（非容器）跑 Isaac Sim WebRTC 曾長期黑畫面，當時的結論（**本次未重新驗證**）：

- 根因：headless + `--livestream` 下 Kit 事件迴圈被推得不夠快，影格進不了 NVENC。
  修法是每次 `sim.step()` **之前**多呼叫幾次 `omni.kit.app.get_app().update()`
  （放在 `render()` 內會讓 PhysX tensor view 失效）。
- 必要條件：啟動帶
  `--kit_args "--/exts/omni.kit.livestream.app/primaryStream/publicIp=<可被客戶端連到的 IP>"`；
  同時只能有一個 Isaac Sim instance（否則 `NVST_R_BUSY`）。
- 相關檔案（存在 [已驗證]）：`~/isaac_viewer.py`、`~/viewer_launch.py`、`~/IsaacLab/view.sh`。
- `nvidia-smi -q -d ENCODER_STATS` 的 Average FPS 常顯示 0，不能當成敗依據。

## 附錄 B：接入 `parcel-forge` 專案的注意事項（[未驗證]）

你的專案 `github.com/wyattsheu/parcel-forge`（本機 `~/ITRI/parcel-forge`）的 README 寫明是針對
**主機上既有的 Isaac Sim 6.0.1.0 install** 建立，並「re-launch 進既有 Isaac runtime」，路徑集中在
`config/isaac_env.json`。學生容器的組合是 Isaac Sim 6.1.0.0 / venv 在 `/workspace/IsaacLab/.venv`，
**兩者路徑與版本都不同**，接入時需要：

1. 修改 `config/isaac_env.json` 指向容器內的 python / 安裝位置。
2. 預期 6.0.1.0 → 6.1.0.0 可能有行為差異，需重跑其驗證流程再確認。

## 變更紀錄

- 2026-09-28：初版。於學生容器實測 Vulkan、Kit 啟動（`Setup complete`）、版本組合；
  釐清 EULA、`sm_120` 對應的 PyTorch 版本、磁碟用量；更正先前文件誤寫的 Isaac Sim 版本
  （實際為 6.1.0.0，非 6.0.1.0）。
- 2026-09-28（更新）：新增 §6「沒有 root 的情況」——記錄主機是用 `uv` 免 root 安裝、系統 Python 缺 `ensurepip`、
  哪些需求需要 root，以及 A–F 其他方法的比較表；補上主機兩個 venv 的版本對照。
