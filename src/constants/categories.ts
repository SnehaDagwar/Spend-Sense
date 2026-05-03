import type { CategoryBudget } from "@/types";

export const DEFAULT_CATEGORIES: Omit<CategoryBudget, "planned">[] = [
  { id: "food", name: "Food", icon: "UtensilsCrossed", color: "hsl(var(--cat-food))", isCustom: false },
  { id: "shopping", name: "Shopping", icon: "ShoppingBag", color: "hsl(var(--cat-shopping))", isCustom: false },
  { id: "recharge", name: "Recharge", icon: "Smartphone", color: "hsl(var(--cat-recharge))", isCustom: false },
  { id: "transport", name: "Transport", icon: "Bus", color: "hsl(var(--cat-transport))", isCustom: false },
  { id: "rent", name: "Rent", icon: "Home", color: "hsl(var(--cat-rent))", isCustom: false },
  { id: "medical", name: "Medical", icon: "Stethoscope", color: "hsl(var(--cat-medical))", isCustom: false },
  { id: "electricity", name: "Electricity", icon: "Zap", color: "hsl(var(--cat-electricity))", isCustom: false },
  { id: "others", name: "Others", icon: "MoreHorizontal", color: "hsl(var(--cat-others))", isCustom: false },
];

export const SUGGESTED_PLAN: Record<string, number> = {
  food: 8000, shopping: 4000, recharge: 500, transport: 2500,
  rent: 15000, medical: 1500, electricity: 1500, others: 2000,
};
