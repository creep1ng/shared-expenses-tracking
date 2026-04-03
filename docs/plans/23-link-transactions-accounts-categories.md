# Plan de Implementación: Issue #23 - Link Transactions to Accounts and Categories

## Resumen del Issue

Permitir asociar transacciones con Accounts y Categories específicas, haciendo estos campos requeridos para que el dashboard refleje datos reales.

## Análisis del Estado Previo

El issue #23 fue marcado como tech-debt pero la funcionalidad ya estaba implementada en el codebase:

**Backend ya tenía:**
- Modelo `Transaction` con `source_account_id`, `destination_account_id`, `category_id`
- Validación en `TransactionService._validate_transaction_constraints()` que exige:
  - `expense` → `source_account_id` y `category_id` (tipo expense)
  - `income` → `destination_account_id` y `category_id` (tipo income)
  - `transfer` → ambos accounts, sin category
- Repository con `joinedload` para cargar relaciones
- Schema `TransactionResponse` con objetos `source_account`, `destination_account`, `category`

**Frontend ya tenía:**
- Dropdowns en `TransactionForm` para accounts y categories
- Validación Zod en `transactionFormSchema` por tipo de transacción
- Tipos TypeScript con objetos relacionados
- Panel que muestra account/category en detalle expandido

## Lo Que Se Implementó

Se agregaron **6 tests unitarios** para validar la funcionalidad existente:

**Archivo**: `backend/tests/test_transactions.py`

1. `test_expense_requires_source_account_id` - Verifica expense sin source_account_id retorna 422
2. `test_expense_requires_category_id` - Verifica expense sin category_id retorna 422
3. `test_income_requires_destination_account_id` - Verifica income sin destination_account_id retorna 422
4. `test_income_requires_category_id` - Verifica income sin category_id retorna 422
5. `test_transfer_requires_both_accounts` - Verifica transfer sin accounts retorna 422
6. `test_list_transactions_returns_account_and_category_names` - Verifica GET retorna nombres

---

## Definición de Done Checklist

- [x] Migration creada (NO NECESARIA - el modelo ya tiene FK con validación en aplicación)
- [x] POST valida account_id y category_id según tipo de transacción
- [x] GET retorna account_name y category_name (vía objetos relacionados)
- [x] Tests backend pasan (6 tests nuevos agregados)
- [x] Form muestra dropdowns con datos reales
- [x] Validación Zod refleja reglas de negocio
- [x] Panel muestra columnas de Account y Category
- [x] Linting y typecheck pasan
