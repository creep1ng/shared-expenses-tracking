import { requestJson } from "@/lib/api/client";
import type {
  Category,
  CategoryCreatePayload,
  CategoryListResponse,
  CategoryUpdatePayload,
} from "@/lib/categories/types";

type ListCategoriesOptions = {
  includeArchived?: boolean;
};

export function listCategories(
  workspaceId: string,
  options: ListCategoriesOptions = {},
): Promise<CategoryListResponse> {
  const query = options.includeArchived ? "?include_archived=true" : "";

  return requestJson<CategoryListResponse>(`/workspaces/${workspaceId}/categories${query}`, {
    method: "GET",
  });
}

export function createCategory(workspaceId: string, payload: CategoryCreatePayload): Promise<Category> {
  return requestJson<Category>(`/workspaces/${workspaceId}/categories`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCategory(
  workspaceId: string,
  categoryId: string,
  payload: CategoryUpdatePayload,
): Promise<Category> {
  return requestJson<Category>(`/workspaces/${workspaceId}/categories/${categoryId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function archiveCategory(workspaceId: string, categoryId: string): Promise<Category> {
  return requestJson<Category>(`/workspaces/${workspaceId}/categories/${categoryId}/archive`, {
    method: "POST",
  });
}
