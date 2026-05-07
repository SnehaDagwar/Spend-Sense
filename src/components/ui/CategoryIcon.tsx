import { 
  // Category Defaults
  UtensilsCrossed, 
  ShoppingBag, 
  Smartphone, 
  Bus, 
  Home, 
  Stethoscope, 
  Zap, 
  MoreHorizontal,
  
  // Reference Image Icons (Row 1)
  LayoutGrid,
  Users,
  Book,
  FileText,
  Calendar,
  Mail,
  Bell,
  
  // Reference Image Icons (Row 2)
  BarChart3,
  PieChart,
  LineChart,
  Clock,
  Bookmark,
  Star,
  Settings,
  LogOut,
  
  // Reference Image Icons (Row 3)
  PlusSquare,
  Download,
  Upload,
  Filter,
  Search,
  MoreVertical,
  CheckCircle2,
  XCircle,
  
  // Fallback
  HelpCircle,
  
  // Custom
  Dumbbell
} from "lucide-react";
import { cn } from "@/lib/utils";

export const ICON_MAP: Record<string, any> = {
  UtensilsCrossed,
  ShoppingBag,
  Smartphone,
  Bus,
  Home,
  Stethoscope,
  Zap,
  MoreHorizontal,
  LayoutGrid,
  Users,
  Book,
  FileText,
  Calendar,
  Mail,
  Bell,
  BarChart3,
  PieChart,
  LineChart,
  Clock,
  Bookmark,
  Star,
  Settings,
  LogOut,
  PlusSquare,
  Download,
  Upload,
  Filter,
  Search,
  MoreVertical,
  CheckCircle2,
  XCircle,
  Dumbbell,
};

interface CategoryIconProps {
  name: string;
  className?: string;
}

export function CategoryIcon({ name, className }: CategoryIconProps) {
  // Map common custom icon names to valid lucide components
  const normalizedName = name?.toLowerCase() === "gym" || name === "🏋️" ? "Dumbbell" : name;
  const IconComponent = ICON_MAP[normalizedName] || ICON_MAP[name];

  if (!IconComponent) {
    if (name && name.length <= 2) {
      return <span className={cn("text-lg", className)}>{name}</span>;
    }
    return <HelpCircle className={cn("text-primary", className)} />;
  }

  return (
    <IconComponent 
      className={cn("text-primary", className)} 
    />
  );
}
