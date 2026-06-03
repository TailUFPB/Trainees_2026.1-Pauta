"use client";
import { useEffect, useState } from "react";

export type Theme = "light" | "dark";
const STORAGE_KEY = "pauta-theme";

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>("light");

  useEffect(() => {
    // Sync state with theme set by no-flash inline script before hydration.
    const current = (document.documentElement.dataset.theme as Theme) || "light";
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setThemeState(current);
  }, []);

  const setTheme = (t: Theme) => {
    setThemeState(t);
    document.documentElement.dataset.theme = t;
    try {
      localStorage.setItem(STORAGE_KEY, t);
    } catch {}
  };

  const toggle = () => setTheme(theme === "dark" ? "light" : "dark");

  return { theme, setTheme, toggle };
}
