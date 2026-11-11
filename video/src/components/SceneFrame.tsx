import React, { type CSSProperties, type ReactNode } from "react";
import { AbsoluteFill } from "remotion";
import { COLORS, SAFE } from "../theme";

/** Cena em tela cheia: fundo compartilhado e margem de segurança. */
export const SceneFrame: React.FC<{
  children: ReactNode;
  style?: CSSProperties;
}> = ({ children, style }) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        paddingTop: SAFE.top,
        paddingRight: SAFE.x,
        paddingBottom: SAFE.bottom,
        paddingLeft: SAFE.x,
        ...style,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
