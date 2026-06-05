import { useEffect, useState } from "react";

type Theme = "dark" | "light";

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem("failsage-theme");
    return (saved === "light" ? "light" : "dark") as Theme;
  });

  useEffect(() => {
    const html = document.documentElement;
    // Tailwind darkMode:"class" — presence of "dark" class enables dark variants
    html.classList.toggle("dark", theme === "dark");
    localStorage.setItem("failsage-theme", theme);
  }, [theme]);

  const toggle = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  return { theme, toggle };
}
