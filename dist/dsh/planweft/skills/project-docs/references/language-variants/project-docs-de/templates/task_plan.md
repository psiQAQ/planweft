# Aufgabenplan: [Kurze Beschreibung]

Nutzen Sie diese Datei als dauerhafte Roadmap für die Aufgabe. Erstellen Sie sie vor komplexer Arbeit und halten Sie sie bei jedem Phasenwechsel aktuell.

## Ziel

Beschreiben Sie das angestrebte Endergebnis in einem klaren Satz.

[Ein Satz, der den Endzustand beschreibt]

## Nächster Schritt

Notieren Sie die eine Aktion, die als Nächstes erfolgen soll. Aktualisieren Sie sie, wenn sich die aktive Phase oder die unmittelbare Aktion ändert.

[Die nächste einzelne Aktion. Bei jedem Phasenwechsel aktualisieren.]

## Aktuelle Phase

Benennen Sie die Phase, die gerade bearbeitet wird.

Phase 1

## Phasen

Gliedern Sie die Aufgabe in drei bis sieben überprüfbare Phasen. Verwenden Sie für jeden Status nur `pending`, `in_progress` oder `complete` und aktualisieren Sie den Wert, sobald die Arbeit fortschreitet.

### Phase 1: Anforderungen & Erkundung

- [ ] Nutzerintention verstehen
- [ ] Einschränkungen und Anforderungen identifizieren
- [ ] Ergebnisse in findings.md dokumentieren
- **Status:** in_progress

### Phase 2: Planung & Struktur

- [ ] Technischen Ansatz definieren
- [ ] Projektstruktur bei Bedarf erstellen
- [ ] Entscheidungen mit Begründung dokumentieren
- **Status:** pending

### Phase 3: Umsetzung

- [ ] Den Plan Schritt für Schritt ausführen
- [ ] Code vor der Ausführung in Dateien schreiben
- [ ] Inkrementell testen
- **Status:** pending

### Phase 4: Testen & Überprüfung

- [ ] Erfüllung aller Anforderungen überprüfen
- [ ] Testergebnisse in progress.md dokumentieren
- [ ] Gefundene Probleme beheben
- **Status:** pending

### Phase 5: Übergabe

- [ ] Alle Ausgabedateien überprüfen
- [ ] Vollständigkeit der Lieferobjekte sicherstellen
- [ ] An den Nutzer übergeben
- **Status:** pending

## Schlüsselfragen

Notieren Sie wichtige Fragen und ersetzen Sie sie durch Antworten, sobald sie geklärt sind.

1. [Zu beantwortende Frage]
2. [Zu beantwortende Frage]

## Getroffene Entscheidungen

Notieren Sie bedeutende Entscheidungen und die jeweilige Begründung.

| Entscheidung | Begründung |
|-------------|-----------|
|             |           |

## Aufgetretene Fehler

Notieren Sie jeden unterschiedlichen Fehler, die Nummer des Versuchs und die Lösung. Ändern Sie den Ansatz, bevor Sie eine fehlgeschlagene Aktion erneut versuchen.

| Fehler | Versuch | Lösung |
|--------|---------|--------|
|        | 1       |        |

## Hinweise

- Aktualisieren Sie den Phasenstatus im Verlauf der Arbeit von `pending` zu `in_progress` und danach zu `complete`.
- Prüfen Sie Ziel und nächsten Schritt vor wichtigen Entscheidungen erneut.
- Protokollieren Sie Fehler zeitnah, damit fehlgeschlagene Ansätze nicht wiederholt werden.

## Scope and acceptance evidence

Keep only fields useful to this task. Link existing approved requirements instead of copying them into a second specification. This selected plan is the single dynamic task-status source.

- Scope source: keep authorized targets, prohibited reads/writes and verification limits with their actual instruction sources in the existing Goal section within the first 30 lines; do not duplicate live boundaries here.
- Success criteria and requirement source: [observable result and exact reference]
- Verification evidence: [progress entry or reproduction record; actual Passed, Failed or Not Run]
- Stable design records: [affected specification or ADR, only if needed]
- Plan owner and worker record locations: [owner and assigned records, when using multiple agents]

## Handoff evidence

Keep the current next action in `## Next Step` above, rather than duplicating a live task list here.

- Remaining blocker or approval decision: [concrete missing input, or none]
- Independent evidence review: [record and disposition, or Not Run with reason]
- Fresh-reader check: [record and discrepancy resolution, or Not Run with reason]
- Existing plan migration: [old status entry now points here, when the target project adopts this workflow; otherwise not applicable]

Attestation records bytes, not approval. Checked phases or a gate decision do not prove that acceptance criteria passed.
