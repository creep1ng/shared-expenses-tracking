"use client";

import React, { useEffect, useRef, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { transactionFormSchema, type TransactionFormValues } from "@/lib/transactions/schemas";
import {
  buildTransactionPayload,
  getCurrentDateTimeInputValue,
  getSelectableTransactionCategories,
  TRANSACTION_TYPE_OPTIONS,
} from "@/lib/transactions/presentation";
import type { Account } from "@/lib/accounts/types";
import type { Category } from "@/lib/categories/types";
import type { TransactionCreatePayload } from "@/lib/transactions/types";

type QuickAddModalProps = {
  isOpen: boolean;
  onClose: () => void;
  workspaceId: string;
  accounts: Account[];
  categories: Category[];
  onSubmitTransaction: (payload: TransactionCreatePayload) => Promise<boolean>;
};

export function QuickAddModal({
  isOpen,
  onClose,
  accounts,
  categories,
  onSubmitTransaction,
}: QuickAddModalProps) {
  const [isPending, setIsPending] = useState(false);
  const amountInputRef = useRef<HTMLInputElement>(null);

  const form = useForm<TransactionFormValues>({
    resolver: zodResolver(transactionFormSchema),
    defaultValues: {
      type: "expense",
      sourceAccountId: "",
      destinationAccountId: "",
      categoryId: "",
      amount: "",
      occurredAt: getCurrentDateTimeInputValue(),
      description: "",
      isSplit: false,
      splits: [],
      tags: [],
      location: "",
    },
    mode: "onChange",
  });

  const transactionType = useWatch({ control: form.control, name: "type" });
  const selectableCategories = getSelectableTransactionCategories(categories, transactionType);

  useEffect(() => {
    if (isOpen) {
      form.reset({
        type: "expense",
        sourceAccountId: "",
        destinationAccountId: "",
        categoryId: "",
        amount: "",
        occurredAt: getCurrentDateTimeInputValue(),
        description: "",
      });
      setTimeout(() => amountInputRef.current?.focus(), 100);
    }
  }, [isOpen, form]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (!isOpen) onClose();
      }
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const onSubmit = form.handleSubmit(async (values) => {
    setIsPending(true);
    try {
      const payload = buildTransactionPayload(values, accounts);
      const success = await onSubmitTransaction(payload);
      if (success) {
        onClose();
      }
    } finally {
      setIsPending(false);
    }
  });

  return (
    <Dialog open={isOpen} onOpenChange={(open: boolean) => !open && onClose()}>
      <DialogContent className="sm:max-w-[520px] p-0 gap-0 overflow-hidden">
        <DialogHeader className="p-4 pb-2">
          <DialogTitle className="text-xl font-medium">Nuevo movimiento</DialogTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Registra gastos, ingresos o transferencias en 3 segundos
          </p>
        </DialogHeader>

        <form onSubmit={onSubmit} className="p-4 pt-2">
          <Tabs
            defaultValue="expense"
            value={transactionType}
            onValueChange={(v: string) => form.setValue("type", v as "income" | "expense" | "transfer", { shouldValidate: true })}
            className="w-full"
          >
            <TabsList className="grid grid-cols-3 w-full mb-4">
              {TRANSACTION_TYPE_OPTIONS.map((option) => (
                <TabsTrigger key={option.value} value={option.value} className="py-2">
                  {option.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>

          <div className="space-y-3">
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <Input
                  type="text"
                  inputMode="decimal"
                  placeholder="0.00"
                  className="text-2xl font-medium h-12 text-center"
                  {...form.register("amount")}
                />
                {form.formState.errors.amount && (
                  <p className="text-xs text-destructive mt-1">{form.formState.errors.amount.message}</p>
                )}
              </div>

              <Select
                value={form.watch("categoryId")}
                onValueChange={(v: string) => form.setValue("categoryId", v, { shouldValidate: true })}
              >
                <SelectTrigger className="w-[180px] h-12">
                  <SelectValue placeholder="Categoría" />
                </SelectTrigger>
                <SelectContent>
                  {selectableCategories.map((category) => (
                    <SelectItem key={category.id} value={category.id}>
                      {category.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Textarea
              placeholder="¿Qué fue? (opcional)"
              rows={2}
              className="resize-none"
              {...form.register("description")}
            />

            {transactionType !== "income" && (
              <Select
                value={form.watch("sourceAccountId")}
                onValueChange={(v: string) => form.setValue("sourceAccountId", v, { shouldValidate: true })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Cuenta origen" />
                </SelectTrigger>
                <SelectContent>
                  {accounts.map((account) => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.name} ({account.currency})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}

            {transactionType !== "expense" && (
              <Select
                value={form.watch("destinationAccountId")}
                onValueChange={(v: string) => form.setValue("destinationAccountId", v, { shouldValidate: true })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Cuenta destino" />
                </SelectTrigger>
                <SelectContent>
                  {accounts.map((account) => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.name} ({account.currency})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          <div className="flex justify-end gap-2 mt-6">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Guardando..." : "Guardar movimiento"}
            </Button>
          </div>
        </form>

        <div className="px-4 py-3 bg-muted/30 text-xs text-muted-foreground border-t flex justify-between">
          <span>Atajo global: ⌘K</span>
          <span>Envía con ⏎</span>
        </div>
      </DialogContent>
    </Dialog>
  );
}
