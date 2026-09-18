# WF-P1：離線預處理與生成前檢查

Status: in_progress
Depends on: WF-P0

下一步實作 standard-library-only 的 bundle validator 與可執行 preflight CLI；讀取同一 capability/task registry，輸出需求缺口與 test selection，不生成物體。
拒絕未知欄位／版本、無效引用、非有限數值、必要 runtime 遺失、禁止簡化；unsupported、needs_input、conflict 與 ready_for_planning 分開。
驗證四種 P0 範例及負向 fixtures；只改 intended_task 的搬運→解包案例必須增加釋放能力需求。
來源檢索結果以 source cards 明確保存，沒有真值不冒充測量。後續網路／自然語言自動化分小卡接入，不能在離線 CLI 尚未通過前稱完整 P1 已完成。
不使用開关按鈕、不動 Isaac 環境。

## 已實作／已驗證

離線 CLI 已實作；11 個防線測試與四例 CLI 已跑，證據 runs/20260917T165222Z_wf_p1_checks。
未完成：參數欄位型別／維度／來源卡的完整嚴格驗證、自然語言需求補全、網路檢索快取。尚未進入 P2。

## 單一案例範圍更新

使用者要求少測：主要端到端案例固定 carton_keyboard，不跑其他新物件組合。必要錯誤防線保留，但不做廣泛矩陣掃描。
已補參數 scalar/finite/units/positive/source card 與複合 task 需求。來源檢索／自然語言補全仍未完成。

单一 keyboard fixture 已生成／受力實測，runs/20260917T235608Z_keyboard_package。這是代表性整合實驗，不代表 P1 全部完成或 payload_extraction 已支援。下一步維持此一案例。

## 可移動性修正

free 必含 structure.mobility；機器人搬運／取出任務 fixed 拒絕。13 防線 tests exit 0；單例物理 runs/20260918T001602Z_keyboard_package 驗无世界錨定／dynamic／推力位移。P1 完整來源／語義補全尚未完成。

交付盤點確認：workflow preflight 未被 pf-keyboard-package 呼叫，生成未讀 bundle。先接通契約與生成，不能以局部 hardcoded 物理成功宣稱 P1/通用 gate 完成。詳見 reports/development/2026-09-18_final_delivery_audit.md。

## 圖片擴展調查（2026-09-18）

圖片入口只有規劃，尚未安裝／生成。詳細方案：docs/research/IMAGE_TO_3D_IMPLEMENTATION.md。仍用紙箱裝鍵盤單例，先接 bundle gate，再做單後端資格測試。本次僅研究，未重跑物理、不新增 pass。證據：runs/20260918T005858Z_image_provider_research。

圖片單例更正：使用者不要箱內鍵盤，改單一手持電鑽，測圖片外形生成與剛體可互動。詳見 IMAGE_TO_3D_IMPLEMENTATION.md；尚未生成。
