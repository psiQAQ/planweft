---
name: project-docs-de
description: "Use for implementation/maintenance with investigation, fixes, regression tests and handoff, including existing notes. Read-only/trivial tasks do not initialize files. Use the host-listed Skill path; read it before resource lookup. Do not use host settings or installation receipts to locate resources. Kiro skill instructions and steering state read selected project planning context; recovery reads project files and timestamps only, not agent transcript stores. It registers no Stop hook and never requests continuation. It never runs commands declared in Markdown; no network upload path. "
metadata:
  version: "0.4.0-rc.11"
---

# Projektdokumentation und Aufgabenplanung

Nutze diese vier Schritte für Wartung oder Implementierung mit Untersuchung, Änderungen, Regressionstests und dauerhafter Übergabe. Beurteile die ganze Aufgabe, nicht die Größe des Code-Diffs. Antworte in der Sprache des Nutzers.

## 1. Umfang klären und Projekteinstieg lesen

Lies Projektanweisungen, genehmigte Anforderungen, vorhandene Notizen und relevante Diffs. Bewahre Änderungen des Nutzers. Lesen, Diagnose und Planungsmodus des Hosts bleiben schreibgeschützt: keine Projektaufzeichnungen anlegen oder ändern. Triviale Aufgaben benötigen keinen neuen Plan. Ein ausdrücklich gewünschtes Forschungsdokument erlaubt dieses Dokument, keine zusätzliche Planungshierarchie.

Wenn neue Dateien, die Übernahme oder ein Wechsel der Autorität des alten Plans ausdrücklich verboten sind, zitiere die tatsächliche Anweisung und behalte diese Autorität. Allgemeine Hinweise auf minimale Änderungen oder Wiederverwendung begründen diese Ausnahme nicht. Für autorisierte Implementierung folgt die Vorbereitung.

Verwende den vom Host angegebenen `SKILL.md`-Pfad für Paketressourcen. Das cwd der Skripte ist das autorisierte Projekt. Suche Ressourcen nicht in Host-Konfiguration, Installationsbelegen oder fremden Umgebungsvariablen; prüfe bei Bedarf nur `PLAN_ID`, `PWF_*` und `PLANNING_DISABLED` für die Helfer.

## 2. Aufgabe vor der Implementierung vorbereiten

Lies [Planauswahl](references/plan-selection.md) ([中文](references/plan-selection.zh.md)); führe `sh "<installierter Skill>/scripts/resolve-plan-dir.sh"` oder das dokumentierte PowerShell-Gegenstück aus. Leere Ausgabe bei Exitcode 0 bedeutet allein nicht, dass kein Plan existiert. Prüfe Bindungen einschließlich `PWF_PLAN_ROOT` und tatsächliche Projektdateien:

- Gültiger ausgewählter Plan: alle drei Aufzeichnungen lesen und fortsetzen.
- Abgelehnte Bindung oder mehrdeutige Auswahl: vor Schreibzugriffen korrigieren, keinen anderen Plan anlegen.
- Weder Plan noch ungeklärte Bindung vorhanden, Implementierung autorisiert: `bash "<installierter Skill>/scripts/init-session.sh" "Task Name"` oder den dokumentierten Initialisierer ausführen. Tatsächlich angelegte Dateien prüfen und vor Implementierung ausfüllen; zurückgegebene `PLAN_ID` behalten.

Vor der Implementierung eine knappe Bereichszusammenfassung mit den tatsächlichen Benutzer-/Projektquellen im bestehenden Zielabschnitt innerhalb der ersten 30 Zeilen festhalten: erlaubte Ziele, verbotene Lese-/Schreibzugriffe und Prüfgrenzen. Die konkreten Aufgabenanweisungen einschließen, nicht nur allgemeine Projektregeln. Diese Zusammenfassung dort einmalig pflegen; Erinnerungen können nur den Plananfang oder Goal auswählen. Der Plan dokumentiert Berechtigungen, er erteilt sie nicht. Bei neu initialisierten Plänen diese eine Überschrift als `## Goal` schreiben und die Sprache im Text beibehalten; kein zweites Ziel anlegen. Geschützte bestehende Überschriften erhalten: Smart-Extraktion kann lokalisierte Ziele auslassen, deshalb dann den vollständigen Plan lesen statt auf Erinnerungen zu vertrauen.

Übertrage den aktuellen Aufgabenstand in `task_plan.md`. Ersetze nur Status/Nächster-Schritt des alten Einstiegs durch einen relativen Link darauf. Bewahre Historie und genehmigte Anforderungen. Eine dynamische Statusquelle, keine bidirektionale Synchronisierung.

## 3. Implementieren und Beobachtungen festhalten

`task_plan.md` enthält Ziel, Phasen, Status, nächste Aktion, Blockaden und Beleglinks. `findings.md` enthält Quellen, datierte Beobachtungen, Annahmen und mögliche Entscheidungen. `progress.md` enthält Aktionen, Fehler und Verifikation. Vor Entscheidungen den Plan erneut lesen, nach jeder Phase aktualisieren. `### Phase` und die Literale `**Status:** pending`, `in_progress`, `complete` erhalten.

Betroffene dauerhafte Dokumente an ihren vorhandenen Orten pflegen; nur nützliche fehlende Aufzeichnungen ergänzen. Genehmigte Anforderungen nicht an den Code anpassen. Ein owner pflegt gemeinsamen Status, workers ihre zugewiesenen Aufzeichnungen; unabhängige Aufgaben verwenden getrennte Pläne/worktrees. Manuelle temporäre Kopien und Gegenproben gehören in aufgabeneigene Verzeichnisse innerhalb des autorisierten Projekts; keine fremden festen Pfade bereinigen.

Tatsächlich ausgeführte Prüfungen mit Befehl oder Aktion, beobachtetem Ergebnis und verfügbarem Exitstatus dokumentieren. Übernommene Ergebnisse nennen die ursprüngliche Aufzeichnung; nicht ausgeführte Prüfungen sind **Not Run**. Codelesen ist keine Ausführung; spätere Ausführung ist kein früheres Ergebnis.

## 4. Aufzeichnungen prüfen und übergeben

Anforderungen, tatsächliches Verhalten und finalen Diff vergleichen. Für jeden Fehler oder spätere Korrektur die noch als aktuell dargestellte Quellaussage berichtigen, oder die alte Beobachtung datieren und ihre Korrektur verlinken. Anschließend diese Aussagen und Belege tatsächlich erneut lesen. Historische Beobachtungen erhalten, nicht in Endverhalten umschreiben.

**Passed**, **Failed**, **Not Run** mit Grenzen berichten. Neue Leser unterscheiden historische Passed von nicht wiederholten und tatsächlich selbst ausgeführten Prüfungen. Den Weg vom alten Einstieg zur einzigen aktuellen Planung prüfen und eine klare nächste Aktion hinterlassen.

Für wesentliche Entwürfe unabhängige Quellenreviewer, für wichtige Übergaben neue Leser einsetzen. Diese erhalten nur Projektdateien, keinen alten Chat und keine erwarteten Antworten. [Belegleitfaden](references/evidence.md) nutzen, Befunde bearbeiten; nicht verfügbare unabhängige Prüfung als Not Run markieren.

[PWF-Details](references/pwf-workflow.md) und [Steuerung](references/controls.md) bei Bedarf lesen. Standard: Hinweise; automatische Wiederaufnahme nur aus Projektdateien, Sitzungshistorie nur auf ausdrückliche Anfrage, attestation ist keine Genehmigung. Nur ein Planungsplugin mit Ausführungshooks je Sitzung. `PLAN_ID`, `PWF_*`, `PLANNING_DISABLED` erhalten; bei Bedarf vor Nur-Lese-Sitzungen `PLANNING_DISABLED=1` setzen. Private Caches getrennt halten; Host-Fähigkeiten gemäß `INSTALL.md`.

Vorlagen für fehlende Aufzeichnungen: [Plan](templates/task_plan.md), [Befunde](templates/findings.md), [Fortschritt](templates/progress.md).
