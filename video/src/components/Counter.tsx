import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

/** Inteiro que conta de 0 até `to` entre os frames locais `fromFrame` e `toFrame`. */
export const Counter: React.FC<{
  to: number;
  fromFrame: number;
  toFrame: number;
}> = ({ to, fromFrame, toFrame }) => {
  const frame = useCurrentFrame();
  const value = Math.round(
    interpolate(frame, [fromFrame, toFrame], [0, to], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }),
  );

  return <span style={{ fontVariantNumeric: "tabular-nums" }}>{value}</span>;
};
