export const formatINR = (n: number, opts: { compact?: boolean } = {}) => {
  if (opts.compact && Math.abs(n) >= 1000) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency", currency: "INR", notation: "compact", maximumFractionDigits: 1,
    }).format(n);
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 0,
  }).format(n);
};

export const formatPercent = (n: number, digits = 0) =>
  `${n.toFixed(digits)}%`;

export const monthLabel = (month: string) => {
  const [y, m] = month.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("en-IN", { month: "long", year: "numeric" });
};

export const currentMonth = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
};

export const daysInMonth = (month: string) => {
  const [y, m] = month.split("-").map(Number);
  return new Date(y, m, 0).getDate();
};

export const dayOfMonth = (month: string) => {
  const today = new Date();
  const [y, m] = month.split("-").map(Number);
  if (today.getFullYear() === y && today.getMonth() + 1 === m) return today.getDate();
  if (today < new Date(y, m - 1, 1)) return 0;
  return daysInMonth(month);
};
