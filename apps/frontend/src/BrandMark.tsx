import type { CSSProperties } from "react";

const whiteMark = new URL("../public/images/nightline-food-cactus-white.svg", import.meta.url).href;
const blackMark = new URL("../public/images/nightline-food-cactus-black.svg", import.meta.url).href;

export function BrandMark({
  surface = "dark",
  size = 44,
}: {
  surface?: "dark" | "light";
  size?: number;
}) {
  return (
    <span
      className={`nightline-mark nightline-mark-${surface}`}
      style={{ "--mark-size": `${size}px` } as CSSProperties}
      aria-hidden="true"
    >
      <img src={surface === "dark" ? whiteMark : blackMark} alt="" width={1024} height={1024} />
    </span>
  );
}
