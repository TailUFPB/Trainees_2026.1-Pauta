import { cn } from "@/lib/design/cn";

interface Props {
  value: string;
  label: string;
  hint?: string;
  className?: string;
}

export function Stat({ value, label, hint, className }: Props) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="font-mono text-[length:clamp(2.5rem,1.5rem+4vw,4rem)] font-semibold tabular-nums leading-none tracking-tight text-text">
        {value}
      </div>
      <div className="text-sm text-text-muted">{label}</div>
      {hint ? <div className="text-xs text-text-muted/80">{hint}</div> : null}
    </div>
  );
}
