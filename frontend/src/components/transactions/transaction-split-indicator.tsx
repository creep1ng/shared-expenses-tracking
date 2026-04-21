"use client";

import React from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Transaction } from "@/lib/transactions/types";
import type { WorkspaceMember } from "@/lib/workspaces/types";
import { formatMinorUnitsAsCurrency } from "@/lib/accounts/presentation";

type SplitMemberAllocation = {
  user_id: string;
  amount_minor: number;
  percentage: number;
  is_payer: boolean;
};

type TransactionSplitIndicatorProps = {
  transaction: Transaction;
  members: WorkspaceMember[];
  currentUserId: string;
};

export function TransactionSplitIndicator({
  transaction,
  members,
  currentUserId,
}: TransactionSplitIndicatorProps) {
  if (!transaction.split_config) {
    return null;
  }

  const allocations: SplitMemberAllocation[] = (transaction.split_config?.splits ?? []).map((item) => ({
    user_id: item.user_id,
    amount_minor: item.amount_minor,
    percentage: item.percentage ?? 0,
    is_payer: transaction.paid_by_user_id === item.user_id,
  }));

  const currentUserAllocation = allocations.find((a) => a.user_id === currentUserId);

  const getMemberLabel = (userId: string) => {
    const member = members.find((m) => m.user_id === userId);
    return member?.email || userId;
  };

  const getMemberInitials = (userId: string) => {
    const label = getMemberLabel(userId);
    return label
      .split(" ")
      .map((w) => w[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  };

  const getBalanceStatus = () => {
    if (!currentUserAllocation) return null;

    const currentUserPaid = transaction.paid_by_user_id === currentUserId;
    const userOwes = currentUserAllocation.amount_minor;

    if (currentUserPaid) {
      const net = transaction.amount_minor - userOwes;
      return {
        type: "positive" as const,
        amount: net,
        label: `Te deben ${formatMinorUnitsAsCurrency(net, transaction.currency)}`,
      };
    } else {
      return {
        type: "negative" as const,
        amount: userOwes,
        label: `Debes ${formatMinorUnitsAsCurrency(userOwes, transaction.currency)}`,
      };
    }
  };

  const balanceStatus = getBalanceStatus();

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-1 cursor-default">
            <div className="flex -space-x-1">
              {allocations.slice(0, 4).map((allocation) => (
                <div
                  key={allocation.user_id}
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-medium border border-background ${
                    allocation.is_payer ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"
                  }`}
                >
                  {getMemberInitials(allocation.user_id)}
                </div>
              ))}
              {allocations.length > 4 && (
                <div className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-medium bg-slate-200 text-slate-600 border border-background">
                  +{allocations.length - 4}
                </div>
              )}
            </div>

            {balanceStatus && (
              <span
                className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                  balanceStatus.type === "positive" ? "bg-emerald-50 text-emerald-600" : "bg-rose-50 text-rose-600"
                }`}
              >
                {balanceStatus.type === "positive" ? "+" : "-"}
                {formatMinorUnitsAsCurrency(balanceStatus.amount, transaction.currency)}
              </span>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent side="left" align="start" className="w-64 p-3">
          <div className="space-y-2">
            <p className="text-xs font-medium text-muted-foreground">Distribución</p>
            <div className="space-y-1.5">
              {allocations.map((allocation) => (
                <div key={allocation.user_id} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-4 h-4 rounded-full flex items-center justify-center text-[8px] ${
                        allocation.is_payer ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {allocation.is_payer ? "✓" : ""}
                    </div>
                    <span className="text-sm">{getMemberLabel(allocation.user_id)}</span>
                  </div>
                  <span className="text-sm font-medium tabular-nums">
                    {formatMinorUnitsAsCurrency(allocation.amount_minor, transaction.currency)}
                  </span>
                </div>
              ))}
            </div>

            {balanceStatus && (
              <div
                className={`mt-2 pt-2 border-t ${
                  balanceStatus.type === "positive" ? "text-emerald-600" : "text-rose-600"
                }`}
              >
                <p className="text-sm font-medium">{balanceStatus.label}</p>
              </div>
            )}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
