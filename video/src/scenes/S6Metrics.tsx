import type { FC } from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, DUR, EASE_OUT, FONTS, SAFE, SCENES, SPRING } from "../theme";

const STAGGER = 50;

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const exitOpacity = (frame: number, duration: number) =>
  interpolate(frame, [duration - DUR.exit, duration], [1, 0], clamp);

type Metric = {
  target: number;
  format: (value: number) => string;
  caption: string;
};

const METRICS: Metric[] = [
  {
    target: 97,
    format: (value) => `✓ ${Math.round(value)}%+`,
    caption: "menos tempo",
  },
  {
    target: 0,
    format: (value) => `✓ $${Math.round(value)}`,
    caption: "de custo · modelo gratuito",
  },
  {
    target: 5,
    format: (value) => `✓ ${Math.round(value)}/5`,
    caption: "análises com código gerado",
  },
];

const MetricCard: FC<{ metric: Metric; index: number }> = ({
  metric,
  index,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const delay = 8 + index * STAGGER;
  const enter = spring({ frame, fps, delay, config: SPRING });
  const value = interpolate(frame, [delay + 4, delay + 40], [0, metric.target], {
    ...clamp,
    easing: EASE_OUT,
  });

  return (
    <div
      style={{
        backgroundColor: COLORS.greenBg,
        color: COLORS.greenInk,
        borderRadius: 22,
        padding: "32px 40px",
        textAlign: "center",
        opacity: interpolate(enter, [0, 1], [0, 1], clamp),
        translate: interpolate(enter, [0, 1], ["0px 36px", "0px 0px"], clamp),
      }}
    >
      <div
        style={{
          fontFamily: FONTS.mono,
          fontWeight: 700,
          fontSize: 96,
          lineHeight: 1,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {metric.format(value)}
      </div>
      <div
        style={{
          marginTop: 12,
          fontFamily: FONTS.sans,
          fontWeight: 600,
          fontSize: 40,
          lineHeight: 1.2,
        }}
      >
        {metric.caption}
      </div>
    </div>
  );
};

export const S6Metrics: FC = () => {
  const frame = useCurrentFrame();

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
        gap: 28,
        opacity: exitOpacity(frame, SCENES.S6Metrics.duration),
      }}
    >
      {METRICS.map((metric, index) => (
        <MetricCard key={metric.caption} metric={metric} index={index} />
      ))}
    </AbsoluteFill>
  );
};
