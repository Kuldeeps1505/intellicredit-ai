import React, { createContext, useContext, useEffect, useState } from "react";

type ThemeName = "blue" | "gold";

interface ThemeContextType {
  theme: ThemeName;
  toggleTheme: () => void;
  themeName: string;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_KEY = "intellicredit-theme";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<ThemeName>(() => {
    const stored = localStorage.getItem(THEME_KEY);
    return stored === "gold" ? "gold" : "blue";
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "gold") {
      root.classList.add("theme-gold");
    } else {
      root.classList.remove("theme-gold");
    }
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === "blue" ? "gold" : "blue"));

  const themeName = theme === "blue" ? "Institutional Blue" : "Classic Gold";

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, themeName }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
