import type { Category, CategoryType } from "@/lib/categories/types";

export const CATEGORY_TYPE_LABELS: Record<CategoryType, string> = {
  income: "Ingreso",
  expense: "Gasto",
};

export const CATEGORY_TYPE_OPTIONS: Array<{ value: CategoryType; label: string }> = [
  { value: "expense", label: CATEGORY_TYPE_LABELS.expense },
  { value: "income", label: CATEGORY_TYPE_LABELS.income },
];

export function getSelectableCategories(
  categories: Category[],
  options: { includeArchived?: boolean } = {},
): Category[] {
  const visibleCategories = options.includeArchived
    ? categories
    : categories.filter((category) => !category.is_archived);

  return [...visibleCategories].sort((left, right) => left.name.localeCompare(right.name, "es"));
}
