import React from "react";
import { useAppStore } from "@/store/useAppStore";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Handshake, ArrowRight } from "lucide-react";

const SplitSettle = () => {
  const { familyMembers, settings } = useAppStore();
  
  const currencySymbol = settings.profile.currency === "INR" ? "₹" : 
                         settings.profile.currency === "USD" ? "$" : "€";

  // Mock data for settlements based on members
  const mockSettlements = familyMembers.length > 1 ? [
    { from: familyMembers[0].name, to: familyMembers[1].name, amount: 1500 },
  ] : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-3 bg-secondary/10 rounded-2xl shadow-sm text-secondary">
          <Handshake className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-3xl font-display font-bold">Split & Settle</h1>
          <p className="text-muted-foreground mt-1">See who owes whom and settle balances.</p>
        </div>
      </div>

      <div className="grid gap-6">
        {mockSettlements.length > 0 ? (
          mockSettlements.map((settlement, idx) => (
            <Card key={idx} className="p-6 glass-card border-none flex items-center justify-between">
              <div className="flex items-center gap-4 text-lg">
                <span className="font-bold">{settlement.from}</span>
                <ArrowRight className="h-5 w-5 text-muted-foreground" />
                <span className="font-bold">{settlement.to}</span>
              </div>
              <div className="flex items-center gap-6">
                <span className="text-2xl font-bold font-display text-secondary">
                  {currencySymbol}{settlement.amount}
                </span>
                <Button className="rounded-full">Settle Up</Button>
              </div>
            </Card>
          ))
        ) : (
          <Card className="p-8 text-center glass-card border-none">
            <Handshake className="h-12 w-12 mx-auto text-muted-foreground/30 mb-4" />
            <h3 className="text-xl font-bold mb-2">All Settled Up!</h3>
            <p className="text-muted-foreground max-w-md mx-auto">
              There are no pending balances between family members. Add shared expenses to start tracking who paid what.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
};

export default SplitSettle;
