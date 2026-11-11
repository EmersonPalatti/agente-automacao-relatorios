import React, { type CSSProperties, type ReactNode } from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { DUR, EASE_OUT } from "../theme";

/** Entra com opacidade e subida em DUR.enter frames, após `delay`. */
export const FadeIn: React.FC<{
  children: ReactNode;
  delay?: number;
  style?: CSSProperties;
}> = ({ children, delay = 0, style }) => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        opacity: interpolate(frame, [delay, delay + DUR.enter], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: EASE_OUT,
        }),
        translate: `0px ${interpolate(frame, [delay, delay + DUR.enter], [28, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: EASE_OUT,
        })}px`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
