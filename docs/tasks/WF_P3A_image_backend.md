# WF-P3A-2：真實圖片後端與USD交付

Status: done (generation / rigid physics / cold-load verified; human pending)
單一物件：手持電鑽。固定開源後端、獨立venv與模型快取，不改Isaac環境。優先可無API key執行且能跳過影片的最小幾何後端；EmbodiedGen保持後續物性/URDF候選。
驗收：真實模型執行、模型/輸入/版本hash、產物交接、USD authoring与落地/外力移動測試、可冷載入viewer指令。人工觀看單列not_tested。不能用程序化代理冒充圖片輸出。

模型generation012226Z、USDphysics012639Z、cold012704Z均exit0；exportimage_drill_v1。人工/render/校準與形狀保真未測。報告：reports/development/2026-09-18_image_drill_delivery.md。
