import type { Variants, Transition } from "motion/react";

export const easeOutExpo = [0.16, 1, 0.3, 1] as const;

export const transitionBase: Transition = {
  duration: 0.25,
  ease: easeOutExpo,
};

export const transitionSlow: Transition = {
  duration: 0.4,
  ease: easeOutExpo,
};

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: transitionBase },
};

export const stagger: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.04, delayChildren: 0.05 },
  },
};

export const slideUp: Variants = {
  hidden: { y: "100%" },
  visible: { y: 0, transition: transitionSlow },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.96 },
  visible: { opacity: 1, scale: 1, transition: transitionBase },
};
