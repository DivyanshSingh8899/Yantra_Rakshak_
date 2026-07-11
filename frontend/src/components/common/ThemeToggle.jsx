export default function ThemeToggle({ theme, onToggle }) {
  const isDark = theme === "dark";
  return (
    <button
      onClick={onToggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="rounded-full h-8 w-8 flex items-center justify-center border border-black/10 dark:border-white/10 text-[#52514e] dark:text-[#c3c2b7] hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
    >
      {isDark ? "☀" : "☽"}
    </button>
  );
}
