export type CategoryType = "income" | "expense";

export type Category = {
  id: string;
  workspace_id: string;
  parent_id: string | null;
  name: string;
  type: CategoryType;
  icon: string;
  color: string;
  archived_at: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
};

export type CategoryListResponse = {
  categories: Category[];
};

export type CategoryCreatePayload = {
  name: string;
  type: CategoryType;
  icon: string;
  color: string;
};

export type CategoryUpdatePayload = Partial<CategoryCreatePayload>;
