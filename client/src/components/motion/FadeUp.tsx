"use client";
import { motion } from "motion/react";
import type { ReactNode } from "react";
import { fadeUp } from "@/lib/design/motion";
import { useReducedMotion } from "@/lib/hooks/useReducedMotion";

interface Props {
  children: ReactNode;
  delay?: number;
  className?: string;
  as?: "div" | "section" | "article" | "li" | "header" | "footer";
}

export function FadeUp({ children, delay = 0, className, as = "div" }: Props) {
  const reduced = useReducedMotion();
  const MotionTag = motion[as];
  if (reduced) {
    const Tag = as;
    return <Tag className={className}>{children}</Tag>;
  }
  return (
    <MotionTag
      className={className}
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2, margin: "0px 0px -10% 0px" }}
      transition={{ delay }}
    >
      {children}
    </MotionTag>
  );
}
