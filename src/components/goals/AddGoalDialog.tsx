import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAppStore } from "@/store/useAppStore";
import { toast } from "sonner";
import { Target, ShieldAlert, Plane, Home, Car, GraduationCap, Laptop } from "lucide-react";

const availableIcons = [
  { name: "Target", icon: Target },
  { name: "ShieldAlert", icon: ShieldAlert },
  { name: "Plane", icon: Plane },
  { name: "Home", icon: Home },
  { name: "Car", icon: Car },
  { name: "GraduationCap", icon: GraduationCap },
  { name: "Laptop", icon: Laptop },
];

const availableColors = [
  "hsl(142.1 76.2% 36.3%)", // Green
  "hsl(217.2 91.2% 59.8%)", // Blue
  "hsl(271.5 81.3% 55.9%)", // Purple
  "hsl(0 84.2% 60.2%)", // Red
  "hsl(31.4 89.6% 53.3%)", // Orange
  "hsl(330 81.3% 60%)", // Pink
];

interface AddGoalDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddGoalDialog({ open, onOpenChange }: AddGoalDialogProps) {
  const addGoal = useAppStore((state) => state.addGoal);

  const [name, setName] = useState("");
  const [targetAmount, setTargetAmount] = useState("");
  const [currentAmount, setCurrentAmount] = useState("");
  const [monthlyContribution, setMonthlyContribution] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [selectedIcon, setSelectedIcon] = useState("Target");
  const [selectedColor, setSelectedColor] = useState(availableColors[0]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!name || !targetAmount || !monthlyContribution) {
      toast.error("Please fill in all required fields.");
      return;
    }

    addGoal({
      name,
      icon: selectedIcon,
      targetAmount: Number(targetAmount),
      currentAmount: Number(currentAmount) || 0,
      monthlyContribution: Number(monthlyContribution),
      targetDate: targetDate ? new Date(targetDate).toISOString() : undefined,
      color: selectedColor,
    });

    toast.success("Goal added successfully!");
    onOpenChange(false);
    
    // Reset form
    setName("");
    setTargetAmount("");
    setCurrentAmount("");
    setMonthlyContribution("");
    setTargetDate("");
    setSelectedIcon("Target");
    setSelectedColor(availableColors[0]);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add New Savings Goal</DialogTitle>
          <DialogDescription>
            Create a new goal to track your savings progress.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label htmlFor="name">Goal Name <span className="text-red-500">*</span></Label>
            <Input
              id="name"
              placeholder="e.g. New Car, Vacation"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="targetAmount">Target Amount <span className="text-red-500">*</span></Label>
              <Input
                id="targetAmount"
                type="number"
                min="1"
                placeholder="0.00"
                value={targetAmount}
                onChange={(e) => setTargetAmount(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="currentAmount">Already Saved</Label>
              <Input
                id="currentAmount"
                type="number"
                min="0"
                placeholder="0.00"
                value={currentAmount}
                onChange={(e) => setCurrentAmount(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="monthlyContribution">Monthly Contribution <span className="text-red-500">*</span></Label>
              <Input
                id="monthlyContribution"
                type="number"
                min="1"
                placeholder="0.00"
                value={monthlyContribution}
                onChange={(e) => setMonthlyContribution(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="targetDate">Target Date (Optional)</Label>
              <Input
                id="targetDate"
                type="date"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <Label>Icon</Label>
            <div className="flex gap-2 flex-wrap">
              {availableIcons.map(({ name: iconName, icon: Icon }) => (
                <button
                  key={iconName}
                  type="button"
                  onClick={() => setSelectedIcon(iconName)}
                  className={`p-2 rounded-lg border transition-colors ${
                    selectedIcon === iconName ? "bg-primary text-primary-foreground border-primary" : "hover:bg-muted"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <Label>Color</Label>
            <div className="flex gap-2">
              {availableColors.map((color) => (
                <button
                  key={color}
                  type="button"
                  onClick={() => setSelectedColor(color)}
                  className={`w-8 h-8 rounded-full border-2 transition-transform ${
                    selectedColor === color ? "scale-110 border-foreground" : "border-transparent"
                  }`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
          </div>

          <DialogFooter className="pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit">Add Goal</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
