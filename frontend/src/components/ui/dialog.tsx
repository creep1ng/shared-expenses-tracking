import React from "react";

type DialogProps = {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
};

type DialogContentProps = {
  className?: string;
  children: React.ReactNode;
};

type DialogHeaderProps = {
  className?: string;
  children: React.ReactNode;
};

type DialogTitleProps = {
  className?: string;
  children: React.ReactNode;
};

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  return (
    <div data-dialog-open={open} onClick={() => onOpenChange?.(!open)}>
      {children}
    </div>
  );
}

export function DialogContent({ className = "", children }: DialogContentProps) {
  return (
    <div data-dialog-content className={className} onClick={(e) => e.stopPropagation()}>
      {children}
    </div>
  );
}

export function DialogHeader({ className = "", children }: DialogHeaderProps) {
  return (
    <div className={className}>
      {children}
    </div>
  );
}

export function DialogTitle({ className = "", children }: DialogTitleProps) {
  return (
    <h2 className={className}>
      {children}
    </h2>
  );
}
