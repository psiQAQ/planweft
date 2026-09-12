# Plan de Tareas: [Breve Descripción]

Esta es la hoja de ruta visible de toda la tarea y la memoria de trabajo persistente en disco. Créala antes de comenzar y actualízala al completar cada fase.

## Objetivo

Escribe una oración clara que describa el estado final. Ejemplo: «Crear una aplicación CLI de tareas en Python con funciones para agregar, listar y eliminar».

[Una oración describiendo el estado final]

## Fase Actual

Indica aquí la fase en curso y actualízala según avances.

Fase 1

## Fases

Divide la tarea en entre 3 y 7 fases que puedan completarse. Actualiza el estado de cada fase con uno de estos valores: `pending`, `in_progress` o `complete`.

### Fase 1: Requisitos y Descubrimiento

Comprende qué se necesita y reúne la información inicial antes de implementar.

- [ ] Entender la intención del usuario
- [ ] Identificar restricciones y requisitos
- [ ] Documentar hallazgos en findings.md
- **Estado:** in_progress

### Fase 2: Planificación y Estructura

Define el enfoque, la estructura y las decisiones técnicas necesarias.

- [ ] Definir enfoque técnico
- [ ] Crear estructura del proyecto si es necesario
- [ ] Documentar decisiones con su justificación
- **Estado:** pending

### Fase 3: Implementación

Ejecuta el plan en pasos pequeños y verifica el trabajo de forma incremental.

- [ ] Ejecutar el plan paso a paso
- [ ] Escribir código en archivos antes de ejecutar
- [ ] Probar incrementalmente
- **Estado:** pending

### Fase 4: Pruebas y Verificación

Comprueba que la solución cumple los requisitos y registra los resultados.

- [ ] Verificar que todos los requisitos se cumplen
- [ ] Documentar resultados de pruebas en progress.md
- [ ] Corregir cualquier problema encontrado
- **Estado:** pending

### Fase 5: Entrega

Revisa los entregables antes de presentarlos al usuario.

- [ ] Revisar todos los archivos de salida
- [ ] Asegurar que los entregables están completos
- [ ] Entregar al usuario
- **Estado:** pending

## Preguntas Clave

Registra las preguntas que guían la investigación y responde cada una cuando dispongas de evidencia.

1. [Pregunta por responder]
2. [Pregunta por responder]

## Decisiones Tomadas

Registra las decisiones técnicas y de diseño junto con su justificación.

| Decisión | Justificación |
|----------|---------------|
|          |               |

## Errores Encontrados

Registra cada error, el número de intento y la resolución. Cambia de enfoque cuando falle una acción en lugar de repetirla sin cambios.

| Error | Intento | Resolución |
|-------|---------|------------|
|       | 1       |            |

## Notas

- Actualiza el estado de la fase según progresas: `pending` → `in_progress` → `complete`.
- Relee este plan antes de decisiones importantes para mantener presente el objetivo aprobado.
- Registra todos los errores para evitar repetirlos.

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
- Active-plan relocation: not supported; record an in-place closure or explicitly authorized archive-index update only when applicable

Attestation records bytes, not approval. Checked phases or a gate decision do not prove that acceptance criteria passed.

## Documentation Handoff

<!-- planweft-docs-status: pending -->

- Documents considered: [affected existing documents, or none]
- Rationale / evidence: [why documentation is needed or not required]
- Next action: [authorized update, verification, or closure action]

The marker has exactly one value: `pending`, `not_required`, or `complete`. It is a
read-only Hook input and not a second task status. Missing, duplicate or malformed
markers remain pending; do not set `complete` before the actual documentation result
is recorded.
