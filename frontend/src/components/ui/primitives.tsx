import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Badge
export const Badge = ({ className, variant = "default", ...props }: any) => {
  const variants: any = {
    default: "bg-primary text-primary-foreground hover:bg-primary/80",
    secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
    destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/80",
    outline: "text-foreground border border-input",
    success: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100",
    warning: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100",
  };
  return (
    <div className={cn("inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none", variants[variant], className)} {...props} />
  );
};

// Card
export const Card = ({ className, ...props }: any) => (
  <div className={cn("rounded-xl border bg-card text-card-foreground shadow", className)} {...props} />
);

// Skeleton
export const Skeleton = ({ className, ...props }: any) => (
  <div className={cn("animate-pulse rounded-md bg-muted", className)} {...props} />
);
