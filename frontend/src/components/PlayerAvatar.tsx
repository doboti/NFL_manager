import { useEffect, useState } from "react";

interface PlayerAvatarProps {
  firstName: string;
  lastName: string;
  photoUrl: string | null;
  size?: number;
}

export default function PlayerAvatar({ firstName, lastName, photoUrl, size = 48 }: PlayerAvatarProps) {
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setFailed(false);
  }, [photoUrl]);
  const initials = `${firstName[0] ?? ""}${lastName[0] ?? ""}`.toUpperCase();

  if (photoUrl && !failed) {
    return (
      <img
        src={photoUrl}
        alt={`${firstName} ${lastName}`}
        loading="lazy"
        onError={() => setFailed(true)}
        className="shrink-0 rounded-full bg-slate-800 object-cover"
        style={{ width: size, height: size }}
      />
    );
  }

  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-full bg-gridiron-field text-xs font-bold text-white"
      style={{ width: size, height: size }}
    >
      {initials}
    </div>
  );
}
