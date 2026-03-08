export type User = {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AuthenticatedUserResponse = {
  user: User;
};

export type MessageResponse = {
  message: string;
};

export type PasswordResetRequestResponse = MessageResponse & {
  reset_token: string | null;
};

export type SignInPayload = {
  email: string;
  password: string;
};

export type SignUpPayload = SignInPayload;

export type PasswordResetRequestPayload = {
  email: string;
};

export type PasswordResetConfirmPayload = {
  token: string;
  new_password: string;
};
