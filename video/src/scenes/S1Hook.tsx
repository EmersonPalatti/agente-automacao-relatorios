import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FadeIn } from "../components/FadeIn";
import { SceneFrame } from "../components/SceneFrame";
import { COLORS, EASE_OUT, FONTS, SPRING } from "../theme";

const numberStyle = {
  fontFamily: FONTS.mono,
  fontWeight: 700,
  lineHeight: 1,
  letterSpacing: -3,
  whiteSpace: "nowrap",
} as const;

/** "1h45" com marca-texto e um risco que atravessa o número. */
const ManualTime: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const rise = interpolate(frame, [0, 15], [28, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const strike = interpolate(frame, [18, 34], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  return (
    <div
      style={{
        opacity,
        translate: `0px ${rise}px`,
        position: "relative",
        overflow: "hidden",
        backgroundColor: COLORS.redBg,
        borderRadius: 24,
        padding: "18px 40px 22px",
      }}
    >
      <span style={{ ...numberStyle, fontSize: 176, color: COLORS.redInk }}>1h45</span>
      <div
        style={{
          position: "absolute",
          left: 36,
          right: 36,
          top: "54%",
          height: 14,
          borderRadius: 999,
          backgroundColor: COLORS.redInk,
          translate: "0px -50%",
          scale: `${strike} 1`,
          transformOrigin: "left center",
        }}
      />
    </div>
  );
};

/** "~2 min" chega por baixo, com o sinal de que o tempo caiu. */
const AgentTime: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rise = spring({
    frame,
    fps,
    delay: 32,
    config: { damping: SPRING.damping, mass: SPRING.mass },
  });

  return (
    <div
      style={{
        opacity: rise,
        translate: `0px ${(1 - rise) * 64}px`,
        display: "flex",
        alignItems: "center",
        gap: 22,
        backgroundColor: COLORS.greenBg,
        borderRadius: 24,
        padding: "18px 40px 22px",
      }}
    >
      <span
        style={{
          fontFamily: FONTS.sans,
          fontWeight: 800,
          fontSize: 72,
          lineHeight: 1,
          color: COLORS.greenInk,
        }}
      >
        ✓
      </span>
      <span
        style={{
          ...numberStyle,
          display: "inline-flex",
          alignItems: "baseline",
          gap: 40,
          fontSize: 156,
          color: COLORS.greenInk,
        }}
      >
        <span>~2</span>
        <span>min</span>
      </span>
    </div>
  );
};

const Label: React.FC<{ children: React.ReactNode; delay: number }> = ({ children, delay }) => (
  <FadeIn delay={delay}>
    <div
      style={{
        fontFamily: FONTS.sans,
        fontWeight: 600,
        fontSize: 36,
        lineHeight: 1.2,
        color: COLORS.gray,
        textAlign: "center",
        marginBottom: 14,
      }}
    >
      {children}
    </div>
  </FadeIn>
);

export const S1Hook: React.FC = () => {
  return (
    <SceneFrame>
      <FadeIn delay={0}>
        <div
          style={{
            fontFamily: FONTS.sans,
            fontWeight: 800,
            fontSize: 56,
            lineHeight: 1.1,
            letterSpacing: -1,
            color: COLORS.ink,
            textAlign: "center",
          }}
        >
          Um relatório de operações
        </div>
      </FadeIn>
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 56,
          paddingBottom: 60,
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          <Label delay={4}>na mão · estimado</Label>
          <ManualTime />
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
          <Label delay={32}>com o agente</Label>
          <AgentTime />
        </div>
      </div>
    </SceneFrame>
  );
};
