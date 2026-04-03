# Plan de Implementación: Issue #23 - Link Transactions to Accounts and Categories

## Resumen del Issue

Permitir asociar transacciones con Accounts y Categories específicas, haciendo estos campos requeridos para que el dashboard refleje datos reales.

## Análisis del Modelo Actual

El modelo `Transaction` actual en `backend/src/app/db/models.py:371-440` ya tiene:
- `source_account_id`: UUID | null (para expense/transfer)
- `destination_account_id`: UUID | null (para income/transfer)
- `category_id`: UUID | null (no para transfers)

**Problema**: Estos campos son nullable, pero el issue requiere que sean NOT NULL para expenses e income.

---

## Backend

### 1. Migration: Agregar Constraints y Nuevos Campos

**Archivo**: `backend/alembic/versions/YYYYMMDD_000009_transaction_account_category_required.py`

- Modificar la columna `source_account_id` para que sea `NOT NULL` cuando `type IN ('expense', 'transfer')`
- Modificar la columna `destination_account_id` para que sea `NOT NULL` cuando `type IN ('income', 'transfer')`
- Modificar `category_id` para que sea `NOT NULL` cuando `type IN ('expense', 'income')`

> **Nota**: Dado que SQLAlchemy no soporta fácilmente conditional NOT NULL via FK, considerar:
> - Usar `CHECK` constraints con triggers en PostgreSQL, O
> - Validación a nivel de aplicación (más simple, preferible para MVP)
> - Separar en `expense_account_id` e `income_account_id` (mayor complejidad)

**Decisión recomendada**: Validación en backend + constraints de base de datos más permisivas pero con CHECK triggers.

### 2. Actualizar Endpoint POST /transactions

**Archivo**: `backend/src/app/api/routes/transactions.py`

- Agregar validación: para `expense` → `source_account_id` requerido
- Agregar validación: para `income` → `destination_account_id` requerido
- Agregar validación: para `expense` e `income` → `category_id` requerido
- Para `transfer` → ambos account_id requeridos, category_id null

### 3. Actualizar Endpoint GET /transactions

- Agregar `joinedload` para `source_account` (eager loading)
- Agregar `joinedload` para `destination_account`
- Agregar `joinedload` para `category`
- Modificar schema de respuesta para incluir `account_name` y `category_name`

### 4. Pydantic Schemas

**Archivos**: 
- `backend/src/app/api/schemas/transaction.py`

Agregar campos de lectura:
```python
source_account_name: str | None = None
destination_account_name: str | None = None
category_name: str | None = None
```

### 5. Tests

**Archivo**: `backend/tests/api/test_transactions.py`

- `test_create_expense_requires_account_and_category`
- `test_create_income_requires_account_and_category`
- `test_create_transfer_requires_accounts`
- `test_create_expense_without_account_returns_422`
- `test_create_expense_without_category_returns_422`
- `test_get_transactions_returns_account_and_category_names`

---

## Frontend

### 1. Transaction Form - Dropdowns de Account y Category

**Archivo**: `frontend/src/components/transactions/transaction-form.tsx`

- En `useEffect` al montar, hacer fetch de accounts: `GET /workspaces/{workspace_id}/accounts`
- En `useEffect` al montar, hacer fetch de categories: `GET /workspaces/{workspace_id}/categories`
- Agregar `<select>` para `sourceAccountId` (expense/transfer)
- Agregar `<select>` para `destinationAccountId` (income/transfer)
- Agregar `<select>` para `categoryId` (expense/income)
- Filtrar categories por tipo (expense vs income) basado en el tipo de transacción

### 2. Validación Cliente

- Modificar schema Zod en `frontend/src/lib/transactions/schemas.ts`:
  - Para `expense`: `sourceAccountId` y `categoryId` requeridos
  - Para `income`: `destinationAccountId` y `categoryId` requeridos
  - Para `transfer`: ambos account IDs requeridos, `categoryId` prohibido

### 3. Transactions Panel - Mostrar Account y Category

**Archivo**: `frontend/src/components/transactions/transactions-panel.tsx`

- Modificar tabla para incluir columnas "Account" y "Category"
- Usar `sourceAccountName`/`destinationAccountName` según tipo de transacción
- Mostrar `categoryName` para expenses/income

### 4. API Response Types

**Archivo**: `frontend/src/lib/transactions/types.ts`

Agregar:
```typescript
sourceAccountName?: string
destinationAccountName?: string
categoryName?: string
```

---

## Orden de Implementación Recomendada

1. **Backend - Migration** (para futuras constraints, pero no bloqueante)
2. **Backend - Validación POST** (lógica principal)
3. **Backend - Schema respuesta GET** (JOIN y nombres)
4. **Backend - Tests** (validar lógica)
5. **Frontend - Tipos actualizados** (contratos)
6. **Frontend - Form con dropdowns** (fetch y display)
7. **Frontend - Validación Zod** (cliente)
8. **Frontend - Panel con columnas** (mostrar datos)

---

## Archivos a Modificar

### Backend
- `backend/alembic/versions/` (nuevo archivo)
- `backend/src/app/api/routes/transactions.py`
- `backend/src/app/api/schemas/transaction.py`
- `backend/src/app/db/models.py` (opcional, solo comentarios)
- `backend/tests/api/test_transactions.py`

### Frontend
- `frontend/src/lib/transactions/types.ts`
- `frontend/src/lib/transactions/schemas.ts`
- `frontend/src/components/transactions/transaction-form.tsx`
- `frontend/src/components/transactions/transactions-panel.tsx`
- `frontend/src/lib/api/client.ts` (si se necesita configuración)

---

## Definición de Done Checklist

- [ ] Migration creada
- [ ] POST valida account_id y category_id según tipo de transacción
- [ ] GET retorna account_name y category_name
- [ ] Tests backend pasan
- [ ] Form muestra dropdowns con datos reales
- [ ] Validación Zod refleja reglas de negocio
- [ ] Panel muestra columnas de Account y Category
- [ ] Linting y typecheck pasan
