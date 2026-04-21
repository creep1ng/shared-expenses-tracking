import React from "react";

type SelectProps = {
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
  className?: string;
};

type SelectTriggerProps = {
  className?: string;
  children: React.ReactNode;
};

type SelectContentProps = {
  className?: string;
  children: React.ReactNode;
};

type SelectItemProps = {
  value: string;
  children: React.ReactNode;
  className?: string;
};

export function Select({ value, onValueChange, children, className = "" }: SelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onValueChange?.(e.target.value)}
      className={className}
    >
      {children}
    </select>
  );
}

export function SelectTrigger({ className = "", children }: SelectTriggerProps) {
  return (
    <div className={className}>
      {children}
    </div>
  );
}

export function SelectContent({ className = "", children }: SelectContentProps) {
  return (
    <div className={className}>
      {children}
    </div>
  );
}

export function SelectItem({ value, children, className = "" }: SelectItemProps) {
  return (
    <option value={value} className={className}>
      {children}
    </option>
  );
}

export function SelectValue({ placeholder }: { placeholder?: string }) {
  return <span>{placeholder}</span>;
}
