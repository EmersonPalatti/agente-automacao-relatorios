import React, { type CSSProperties, type ReactNode } from "react";
import { COLORS } from "../theme";

/** Card branco com borda fina e sombra leve. */
export const Card: React.FC<{
  children: ReactNode;
  style?: CSSProperties;
}> = ({ children, style }) => {
  return (
    <div
      style={{
        backgroundColor: COLORS.white,
        border: `1px solid ${COLORS.line}`,
        borderRadius: 28,
        boxShadow: "0 18px 40px rgba(17, 17, 17, 0.06)",
        boxSizing: "border-box",
        ...style,
      }}
    >
      {children}
    </div>
  );
};
