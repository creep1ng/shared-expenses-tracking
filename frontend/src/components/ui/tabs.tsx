import React from "react";

type TabsProps = {
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  className?: string;
  children: React.ReactNode;
};

type TabsListProps = {
  className?: string;
  children: React.ReactNode;
};

type TabsTriggerProps = {
  value: string;
  className?: string;
  children: React.ReactNode;
};

type TabsContentProps = {
  value: string;
  className?: string;
  children: React.ReactNode;
};

export function Tabs({ defaultValue, value, className = "", children }: TabsProps) {
  return (
    <div data-tabs className={className} data-value={value || defaultValue}>
      {children}
    </div>
  );
}

export function TabsList({ className = "", children }: TabsListProps) {
  return (
    <div data-tabs-list className={className}>
      {children}
    </div>
  );
}

export function TabsTrigger({ value, className = "", children }: TabsTriggerProps) {
  return (
    <button data-tabs-trigger={value} type="button" className={className}>
      {children}
    </button>
  );
}

export function TabsContent({ value, className = "", children }: TabsContentProps) {
  return (
    <div data-tabs-content={value} className={className}>
      {children}
    </div>
  );
}
