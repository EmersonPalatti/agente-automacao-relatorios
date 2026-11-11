import React, { type CSSProperties, type ReactNode } from "react";
import { FONTS } from "../theme";

/** Pílula em mono: fundo `bg`, texto `ink`. */
export const Chip: React.FC<{
  bg: string;
  ink: string;
  children: ReactNode;
  style?: CSSProperties;
}> = ({ bg, ink, children, style }) => {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: bg,
        color: ink,
        fontFamily: FONTS.mono,
        fontWeight: 700,
        fontSize: 36,
        lineHeight: 1.2,
        padding: "14px 28px",
        borderRadius: 999,
        whiteSpace: "nowrap",
        ...style,
      }}
    >
      {children}
    </span>
  );
};
