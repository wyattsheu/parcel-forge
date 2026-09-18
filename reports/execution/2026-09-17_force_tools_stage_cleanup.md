# 本次實際運行

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
