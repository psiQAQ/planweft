#!/usr/bin/env bash
# Initialisiert Planungsdateien für eine neue Sitzung
# Verwendung: ./init-session.sh [Projektname]

set -e

PROJECT_NAME="${1:-projekt}"
DATE=$(date +%Y-%m-%d)

echo "Initialisiere Planungsdateien: $PROJECT_NAME"

# task_plan.md erstellen, wenn nicht vorhanden
if [ ! -f "task_plan.md" ]; then
    cat > task_plan.md << 'EOF'
# Aufgabenplan: [Kurze Beschreibung]

Nutzen Sie diese Datei als dauerhafte Roadmap und halten Sie sie bei jedem Phasenwechsel aktuell.

## Ziel
[Ein-Satz-Beschreibung des Endzustands]

## Nächster Schritt
[Die nächste einzelne Aktion. Bei jedem Phasenwechsel aktualisieren.]

## Aktuelle Phase
Phase 1

## Phasen

### Phase 1: Anforderungen & Entdeckung
- [ ] Benutzerabsicht verstehen
- [ ] Einschränkungen und Anforderungen klären
- [ ] Erkenntnisse in findings.md dokumentieren
- **Status:** in_progress

### Phase 2: Planung & Struktur
- [ ] Technischen Ansatz festlegen
- [ ] Projektstruktur bei Bedarf erstellen
- [ ] Entscheidungen mit Begründung dokumentieren
- **Status:** pending

### Phase 3: Implementierung
- [ ] Schrittweise gemäß Plan ausführen
- [ ] Code zuerst in Dateien schreiben, dann ausführen
- [ ] Inkrementell testen
- **Status:** pending

### Phase 4: Test & Validierung
- [ ] Alle Anforderungen geprüft
- [ ] Testergebnisse in progress.md dokumentieren
- [ ] Gefundene Probleme beheben
- **Status:** pending

### Phase 5: Auslieferung
- [ ] Alle Ausgabedateien geprüft
- [ ] Vollständigkeit der Lieferobjekte sicherstellen
- [ ] An Benutzer ausgeliefert
- **Status:** pending

## Schlüsselfragen
1. [Zu beantwortende Frage]
2. [Zu beantwortende Frage]

## Getroffene Entscheidungen
| Entscheidung | Begründung |
|------|------|

## Aufgetretene Fehler
| Fehler | Versuch | Lösung |
|------|---------|---------|

## Hinweise
- Aktualisieren Sie den Phasenstatus von `pending` zu `in_progress` und danach zu `complete`.
- Prüfen Sie Ziel und nächsten Schritt vor wichtigen Entscheidungen erneut.
- Protokollieren Sie Fehler zeitnah und ändern Sie den Ansatz vor einem erneuten Versuch.
EOF
    echo "task_plan.md erstellt"
else
    echo "task_plan.md existiert bereits, überspringe"
fi

# findings.md erstellen, wenn nicht vorhanden
if [ ! -f "findings.md" ]; then
    cat > findings.md << 'EOF'
# Erkenntnisse & Entscheidungen

Für jede Beobachtung zur Implementierung Quelle und Zeitpunkt oder Revision angeben (vor einer Änderung oder nach der Prüfung). Frühere Erkenntnisse erhalten und bei Änderungen eine datierte Korrektur oder neue Evidenz ergänzen. Frühere Beobachtungen nicht als aktuelle Implementierung darstellen.

## Anforderungen
-

## Forschungsergebnisse
-

## Technische Entscheidungen
| Entscheidung | Begründung |
|------|------|

## Aufgetretene Probleme
| Problem | Lösung |
|------|---------|

## Ressourcen
-
EOF
    echo "findings.md erstellt"
else
    echo "findings.md existiert bereits, überspringe"
fi

# progress.md erstellen, wenn nicht vorhanden
if [ ! -f "progress.md" ]; then
    cat > progress.md << EOF
# Fortschrittsprotokoll

## Sitzung: $DATE

### Sitzungsprotokoll
Hier stehen datierte Aktionen und Ergebnisse. Ziel, aktuelle Phase und nächsten Schritt nur in [task_plan.md](task_plan.md) nachlesen; keinen zweiten laufenden Status pflegen.
- **Startzeit:** $DATE

### Ausgeführte Aktionen
-

### Testergebnisse
| Test | Erwartet | Tatsächlich | Status |
|------|---------|---------|------|

### Fehler
| Fehler | Lösung |
|------|---------|
EOF
    echo "progress.md erstellt"
else
    echo "progress.md existiert bereits, überspringe"
fi

echo ""
echo "Planungsdateien initialisiert!"
echo "Dateien: task_plan.md, findings.md, progress.md"
