"use client";

import React, { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

type ModalProps = {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
};

export function Modal({ isOpen, onClose, title, description, children }: ModalProps) {
  const titleId = useId();
  const descriptionId = useId();
  const modalRef = useRef<HTMLDivElement>(null);
  const previouslyFocusedElementRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }

      if (e.key !== "Tab" || !modalRef.current) return;

      const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
      );

      if (focusableElements.length === 0) {
        e.preventDefault();
        modalRef.current.focus();
        return;
      }

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      }

      if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    };

    if (isOpen) {
      previouslyFocusedElementRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      document.addEventListener("keydown", handleKeyDown);
      const previousOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";

      requestAnimationFrame(() => modalRef.current?.focus());

      return () => {
        document.removeEventListener("keydown", handleKeyDown);
        document.body.style.overflow = previousOverflow;
        previouslyFocusedElementRef.current?.focus();
      };
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen || typeof document === "undefined") return null;

  return createPortal(
    <div className="modal-backdrop" onClick={onClose}>
      <div
        ref={modalRef}
        aria-describedby={description ? descriptionId : undefined}
        aria-labelledby={titleId}
        aria-modal="true"
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        tabIndex={-1}
      >
        <div className="modal-header">
          <div>
            <h2 className="workspace-section-title" id={titleId} style={{ margin: 0 }}>{title}</h2>
            {description && <p className="workspace-section-copy" id={descriptionId} style={{ marginTop: "0.25rem" }}>{description}</p>}
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Cerrar modal">
            <X size={20} aria-hidden="true" />
          </button>
        </div>
        <div className="modal-body">
          {children}
        </div>
      </div>
    </div>,
    document.body,
  );
}
