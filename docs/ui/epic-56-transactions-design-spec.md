# Diseño UI/UX Epic #56 Transactions & Expenses

## 1. Quick Add Modal (Atajo global Cmd+K)

### Arquitectura
- **Componente**: `QuickAddModal` en `/frontend/src/components/transactions/quick-add-modal.tsx`
- **Trigger**: `Cmd+K` global disponible en toda la aplicación
- **Estado**: Controlado desde el contexto del workspace

### Características:
- ✅ Flujo minimalista con campos esenciales visibles por defecto
- ✅ Tabs para cambiar rápidamente tipo de movimiento
- ✅ Focus automático en campo de importe
- ✅ Atajos de teclado confirmados
- ✅ Auto-cierre después de submit exitoso
- ✅ Animación de entrada/salida suave

### Flujo:
1. Usuario presiona `Cmd+K` desde cualquier vista
2. Modal se abre con foco automático en importe
3. Selecciona tipo (Gasto por defecto)
4. Ingresa importe y opcionalmente categoría/descripción
5. `Enter` confirma y guarda el movimiento

---

## 2. Visualización de Splits

### Componente: `TransactionSplitIndicator`
- **Ubicación**: Dentro de cada tarjeta de transacción
- **Patrón**: Tooltip con vista compacta y detalle expandido
- **Indicadores visuales**:
  - Avatares pequeños superpuestos por miembro
  - Color diferenciado para quien pagó
  - Badge indicando balance neto del usuario actual:
    - Verde (+): Otros le deben a ti
    - Rojo (-): Tú le debes a otros

### Comportamiento:
- Por defecto: Solo indicadores compactos sin detalles
- Hover: Muestra tooltip con desglose completo de cuanto le corresponde a cada quien
- Color coding consistente en toda la interfaz

---

## 3. Pagos Programados

### Arquitectura de Información:
- Pestaña independiente dentro del Panel de Transacciones
- Header con contador de alertas de pagos próximos
- Banner de advertencia para pagos que vencen en <7 días

### Estados de alerta:
| Plazo | Estilo |
|---|---|
| 0 días (hoy) | Borde rojo + indicador crítico |
| 1-3 días | Borde amarillo + advertencia |
| 4-7 días | Indicador normal |
| >7 días | Sin resaltado |

### Funcionalidades:
- Toggle entre vista "Próximos" y "Todos"
- Acciones inline: Ver detalle, Editar, Pausar
- Botón de creación rápida desde el panel

---

## 4. Consistencia Visual

### Estándares cumplidos:
✅ Usa clases Tailwind existentes del proyecto
✅ Mantiene patrones de diseño de los demás paneles
✅ Responsivo: funciona en mobile y desktop
✅ Accesible: contrastes apropiados, navegación por teclado
✅ Lenguaje consistentemente en Español

### Componentes Reutilizables:
- `QuickAddModal`
- `TransactionSplitIndicator`
- `ScheduledPaymentsPanel`

### Integración pendiente por Frontend Agent:
1. Instalar shadcn/ui componentes requeridos (Dialog, Tabs, Tooltip, Select)
2. Integrar hook de atajo de teclado global
3. Conectar Quick Add Modal al contexto de workspace
4. Integrar Split Indicator en cada tarjeta de transacción
5. Añadir pestaña de Pagos Programados al TransactionsPanel
6. Crear tipos correspondientes en `transactions/types.ts`
7. Añadir tests para cada componente
