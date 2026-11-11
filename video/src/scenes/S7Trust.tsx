import type { FC } from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, DUR, FONTS, SAFE, SCENES, SPRING } from "../theme";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const Line: FC<{
  text: string;
  delay: number;
  color: string;
  fontSize: number;
  fontWeight: number;
}> = ({ text, delay, color, fontSize, fontWeight }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, delay, config: SPRING });

  return (
    <div
      style={{
        fontFamily: FONTS.sans,
        fontWeight,
        fontSize,
        lineHeight: 1.08,
        letterSpacing: fontSize > 48 ? -1.4 : -0.3,
        color,
        opacity: interpolate(enter, [0, 1], [0, 1], clamp),
        translate: interpolate(enter, [0, 1], ["0px 20px", "0px 0px"], clamp),
      }}
    >
      {text}
    </div>
  );
};

export const S7Trust: FC = () => {
  const frame = useCurrentFrame();
  const exit = interpolate(
    frame,
    [SCENES.S7Trust.duration - DUR.exit, SCENES.S7Trust.duration],
    [1, 0],
    clamp,
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        paddingLeft: SAFE.x,
        paddingRight: SAFE.x,
        paddingTop: SAFE.top,
        paddingBottom: SAFE.bottom,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        textAlign: "center",
        opacity: exit,
      }}
    >
      <Line
        text="Os números saem de código executado."
        delay={0}
        color={COLORS.ink}
        fontSize={72}
        fontWeight={800}
      />
      <div style={{ height: 36 }} />
      <Line
        text="O LLM planeja e escreve a partir delas."
        delay={14}
        color={COLORS.gray}
        fontSize={40}
        fontWeight={400}
      />
    </AbsoluteFill>
  );
};
