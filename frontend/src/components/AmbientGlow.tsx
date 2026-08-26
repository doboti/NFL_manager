import { useTeamTheme } from "../context/TeamThemeContext";

/** Large, heavily blurred team-color blobs behind the dashboard content --
 * pure atmosphere, never touches foreground text/contrast. Mounted once
 * per Dashboard render, fixed behind the sidebar+content layout. */
export default function AmbientGlow() {
  const { primary, secondary } = useTeamTheme();

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden" aria-hidden>
      {/* Faint yard-line texture -- a nod to the field itself, kept nearly
          invisible (2% opacity) so it never competes with foreground content. */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "repeating-linear-gradient(90deg, rgba(255,255,255,0.05) 0px, rgba(255,255,255,0.05) 1px, transparent 1px, transparent 96px)",
          opacity: 0.4,
        }}
      />
      <div
        className="absolute -left-32 -top-32 h-[32rem] w-[32rem] rounded-full blur-3xl"
        style={{ backgroundColor: primary, opacity: 0.16 }}
      />
      <div
        className="absolute -right-24 top-1/3 h-[26rem] w-[26rem] rounded-full blur-3xl"
        style={{ backgroundColor: secondary, opacity: 0.13 }}
      />
      <div
        className="absolute bottom-[-10rem] left-1/3 h-[28rem] w-[28rem] rounded-full blur-3xl"
        style={{ backgroundColor: primary, opacity: 0.1 }}
      />
    </div>
  );
}
