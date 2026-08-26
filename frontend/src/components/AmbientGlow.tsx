import { useTeamTheme } from "../context/TeamThemeContext";

/** Large, heavily blurred team-color blobs behind the dashboard content --
 * pure atmosphere, never touches foreground text/contrast. Mounted once
 * per Dashboard render, fixed behind the sidebar+content layout. */
export default function AmbientGlow() {
  const { primary, secondary } = useTeamTheme();

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden" aria-hidden>
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
