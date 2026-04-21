import React from "react";

type TooltipProps = {
  children: React.ReactNode;
};

type TooltipTriggerProps = {
  children: React.ReactNode;
  asChild?: boolean;
};

type TooltipContentProps = {
  className?: string;
  side?: string;
  align?: string;
  children: React.ReactNode;
};

export function Tooltip({ children }: TooltipProps) {
  return (
    <div data-tooltip>
      {children}
    </div>
  );
}

export function TooltipProvider({ children }: TooltipProps) {
  return (
    <div data-tooltip-provider>
      {children}
    </div>
  );
}

export function TooltipTrigger({ children, asChild }: TooltipTriggerProps) {
  return (
    <div data-tooltip-trigger={asChild ? "as-child" : "true"}>
      {children}
    </div>
  );
}

export function TooltipContent({
  className = "",
  side,
  align,
  children,
}: TooltipContentProps) {
  return (
    <div
      data-tooltip-content
      className={className}
      data-side={side}
      data-align={align}
    >
      {children}
    </div>
  );
}
