# 四蓋原型實際執行

## 每一個可確認的小成果

| 項目 | 實測結果 |
| --- | --- |
| 生成四蓋 USD | implemented＋本機生成命令執行完成 |
| articulation 自由度／質量／慣量讀回 | 四 DOFs；tensor readback 保存 |
| 一般物理執行 | pass；2400 steps×4 joints=9600 CSV rows |
| 低力矩主蓋 | peak 14.5846°，終態 -0.1971°，plastic target=0° |
| 高力矩主蓋 | peak約100°，plastic target=30.2248°，終態角16.1549° |
| 高力矩主蓋穩定 | fail；終態速度 .2652 rad/s，不可稱 equilibrium |
| 兩片次蓋塑性／保留開口 | fail；另一主蓋未開，幾何阻擋尚待分離確認 |
| 整體驗收 | fail；未放寬 gate/停用 collision |
| 重複循環疲勞、dt收斂、實物校正 | not_tested（純函式 dt refinement 測試另列） |

原型已證明一片主蓋低負载回復、一片主蓋產生塑性內狀態；尚不能說所有蓋都符合 prompt。
終態角不能用來反推校正，因高力矩主蓋還沒穩定。殘餘平衡還應考慮 joint friction、接觸
與限位，不只是彈性與重力兩項。

