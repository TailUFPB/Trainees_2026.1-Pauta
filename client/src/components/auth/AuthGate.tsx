"use client";
import { cloneElement, isValidElement, type MouseEvent, type ReactElement } from "react";
import { useLoginModal } from "./LoginModalProvider";
import { useSession } from "@/lib/hooks/useSession";

interface Props {
  redirectTo: string;
  children: ReactElement<{ onClick?: (e: MouseEvent) => void }>;
}

export function AuthGate({ redirectTo, children }: Props) {
  const { user, loading } = useSession();
  const { open } = useLoginModal();

  if (!isValidElement(children)) return children;

  const handleClick = (e: MouseEvent) => {
    if (loading) {
      e.preventDefault();
      return;
    }
    if (!user) {
      e.preventDefault();
      open(redirectTo);
      return;
    }
    children.props.onClick?.(e);
  };

  return cloneElement(children, { onClick: handleClick });
}
