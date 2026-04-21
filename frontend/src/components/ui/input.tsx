import React from "react";
import type { InputHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement>;

export function Input({ className = "", ...props }: InputProps) {
  return (
    <input
      className={`w-full px-4 py-3 border border-[rgba(90,60,130,0.18)] rounded-[18px] bg-[rgba(255,255,255,0.72)] text-[var(--foreground)] transition-all duration-180 focus:outline-none focus:border-[var(--accent)] focus:shadow-[0_0_0_4px_rgba(150,103,224,0.12)] ${className}`}
      {...props}
    />
  );
}
