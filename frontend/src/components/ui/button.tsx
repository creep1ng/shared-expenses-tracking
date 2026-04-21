import React from "react";
import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "ghost" | "outline" | "destructive";
  size?: "default" | "sm" | "lg" | "icon";
};

export function Button({
  children,
  className = "",
  variant = "default",
  ...props
}: ButtonProps) {
  const baseClasses = "inline-flex items-center justify-center min-w-[12rem] px-[1.25rem] py-[0.95rem] rounded-[999px] font-bold transition-transform duration-180 hover:-translate-y-0.5";
  
  const variantClasses: Record<string, string> = {
    default: "bg-[var(--accent)] text-white shadow-[0_16px_32px_rgba(150,103,224,0.2)] border-0",
    ghost: "bg-transparent border border-[rgba(90,60,130,0.18)] bg-[rgba(255,255,255,0.54)]",
    outline: "border border-[rgba(90,60,130,0.18)] bg-transparent",
    destructive: "bg-[var(--danger)] text-white",
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
