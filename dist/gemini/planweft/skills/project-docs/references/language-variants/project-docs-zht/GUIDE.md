---
name: project-docs-zht
description: "Use for implementation/maintenance with investigation, fixes, regression tests and handoff, including existing notes. Read-only/trivial tasks do not initialize files. Use the host-listed Skill path; read it before resource lookup. Do not use host settings or installation receipts to locate resources. Uses selected project planning context. Automatic recovery reads project planning files only. Explicit requests only: --metadata / --replay. It never runs commands declared in Markdown; no network upload path. Its session-end hook reports status only and does not request continuation."
metadata:
  version: "0.4.0-rc.10"
---

# 專案文件與任務規劃

包含調查、修改、迴歸驗證和持久交接的實作或維護任務使用以下四步。按整個任務判斷，不按程式碼 diff 大小判斷。使用使用者的語言。

## 1. 明確範圍，閱讀專案入口

閱讀專案指令、核准需求、既有任務記錄及相關 diff，保留使用者修改。閱讀、診斷和宿主規劃模式保持唯讀，不建立或修改專案記錄；簡單任務不需要新計畫。明確要求的書面研究產物只授權該產物，不另行授權規劃層級。

若明確禁止新增檔案、採用新流程或改變舊計畫的權威入口，引用實際指令並保留該權威。「最小修改」「沿用資料」不構成這種例外。其他已授權實作進入任務準備。

資源使用宿主提供的 `SKILL.md` 位置；腳本 cwd 為已授權專案。不要為定位資源檢查宿主設定、安裝收據或無關環境變數；僅按腳本需要查看 `PLAN_ID`、`PWF_*`、`PLANNING_DISABLED`。

## 2. 修改實作前準備任務

先讀[計畫選擇](references/plan-selection.zh.md)（[English](references/plan-selection.md)），再執行 `sh "<安裝 Skill>/scripts/resolve-plan-dir.sh"` 或文件中的 PowerShell 對應入口。空輸出且退出碼 0 本身不等於沒有計畫。結合 `PWF_PLAN_ROOT` 等綁定和實際專案檔案判斷：

- 有有效的所選計畫：閱讀三份記錄並恢復。
- 綁定被拒絕或選擇有歧義：寫入前修正，不另建計畫。
- 既沒有計畫，也沒有待修正綁定，且實作已授權：執行 `bash "<安裝 Skill>/scripts/init-session.sh" "Task Name"` 或文件中的初始化器。檢查實際建立位置，實作前填好記錄；如回傳 `PLAN_ID` 則保留。

將本任務動態狀態轉入所選 `task_plan.md`。僅將舊入口的狀態／下一步欄位替換為指向它的相對連結，保留歷史和核准需求。一個動態狀態來源，不雙向同步。

## 3. 實作並記錄觀察

`task_plan.md` 管理目標、階段、狀態、下一步、阻塞和證據入口；`findings.md` 記錄來源、帶時點的觀察、假設和候選決定；`progress.md` 記錄操作、錯誤和驗證。決策前重讀計畫，每階段後更新；保留解析器字面格式 `### Phase` 和 `**Status:** pending`、`in_progress`、`complete`。

在原有位置維護受影響的長期文件，只建立有用的缺失記錄。不得為配合程式碼改寫核准需求。一個 owner 更新共用狀態，worker 使用分配記錄；獨立任務使用不同計畫或 worktree。手動暫存副本和反事實測試位於授權專案內的本任務自有目錄，不清理非自有固定路徑。

實際執行的檢查記錄命令或操作、觀察結果及可取得的退出狀態；繼承結果引用原記錄；未執行檢查為 **Not Run**。讀碼不是執行，後來的執行不能寫成先前結果。

## 4. 核對記錄並交接

對照需求、實際行為和最終 diff。對每項錯誤或後續更正，修正仍作為當前事實的來源陳述，或給舊陳述標時點並連結更正；隨後實際重讀受影響的陳述及其依據。保留歷史觀察，不改寫成最終行為。

使用 **Passed**、**Failed**、**Not Run** 並說明限制。新讀者分別報告歷史 Passed、本次未重跑項及實際執行的檢查。核對舊入口能到達唯一動態計畫，留下明確下一步。

重要設計使用獨立依據 reviewer，重要交接使用只接收專案檔案的新讀者，不提供舊聊天或預期答案。按[依據指引](references/evidence.md)處理發現；獨立檢查不可用則記 Not Run。

按需閱讀 [PWF 細節](references/pwf-workflow.md)和[控制說明](references/controls.md)。預設提醒模式；自動恢復只用專案檔案，存取會話歷史需明確請求，attestation 不是核准。同一會話只啟用一個規劃外掛的 hooks。保留 `PLAN_ID`、`PWF_*`、`PLANNING_DISABLED`；必要時在唯讀會話啟動前設定 `PLANNING_DISABLED=1`。私有快取與專案記錄分開，宿主能力以 `INSTALL.md` 為準。

缺失記錄範本：[計畫](templates/task_plan.md)、[發現](templates/findings.md)、[進度](templates/progress.md)。
