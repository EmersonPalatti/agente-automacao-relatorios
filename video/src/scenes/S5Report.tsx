import type { FC } from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, DUR, FONTS, SAFE, SCENES, SPRING } from "../theme";

const CARD_W = 560;
const CARD_H = 324;
const GAP = 12;

const SHEETS = [
  { src: "plots/missingness.png", label: "nulos por coluna" },
  { src: "plots/top_city.png", label: "pedidos por cidade" },
  { src: "plots/timeseries.png", label: "volume no tempo" },
] as const;

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const exitOpacity = (frame: number, duration: number) =>
  interpolate(frame, [duration - DUR.exit, duration], [1, 0], clamp);

const Title: FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: SPRING });

  return (
    <div
      style={{
        fontFamily: FONTS.sans,
        fontWeight: 800,
        fontSize: 46,
        lineHeight: 1.12,
        letterSpacing: -0.8,
        color: COLORS.ink,
        opacity: interpolate(enter, [0, 1], [0, 1], clamp),
        translate: interpolate(enter, [0, 1], ["0px 18px", "0px 0px"], clamp),
      }}
    >
      Saída: relatório em Markdown + PDF
    </div>
  );
};

const ReportSheet: FC<{
  src: string;
  label: string;
  index: number;
}> = ({ src, label, index }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const arrive = spring({
    frame,
    fps,
    delay: 8 + (2 - index) * DUR.stagger,
    config: SPRING,
  });
  const open = spring({
    frame,
    fps,
    delay: 34 + index * DUR.stagger,
    config: SPRING,
  });
  const restY = index * (CARD_H + GAP);
  const tilt = [-3.5, 0, 3.5][index] ?? 0;
  const shift = [-26, 0, 26][index] ?? 0;

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        top: 0,
        width: CARD_W,
        height: CARD_H,
        marginLeft: -CARD_W / 2,
        backgroundColor: COLORS.white,
        border: `1px solid ${COLORS.line}`,
        borderRadius: 20,
        boxShadow: "0 10px 28px rgba(17, 17, 17, 0.06)",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        zIndex: 10 - index,
        opacity: interpolate(arrive, [0, 1], [0, 1], clamp),
        scale: interpolate(arrive, [0, 1], [0.96, 1], clamp),
        translate: `${interpolate(open, [0, 1], [0, shift], clamp)}px ${interpolate(open, [0, 1], [0, restY], clamp)}px`,
        rotate: `${interpolate(open, [0, 1], [0, tilt], clamp)}deg`,
      }}
    >
      <div
        style={{
          fontFamily: FONTS.sans,
          fontWeight: 600,
          fontSize: 36,
          lineHeight: 1,
          color: COLORS.gray,
          textAlign: "center",
          padding: "14px 16px 8px",
        }}
      >
        {label}
      </div>
      <div
        style={{
          flex: 1,
          minHeight: 0,
          padding: "0 14px 12px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Img
          src={staticFile(src)}
          style={{ width: "100%", height: "100%", objectFit: "contain" }}
        />
      </div>
    </div>
  );
};

export const S5Report: FC = () => {
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
        opacity: exitOpacity(frame, SCENES.S5Report.duration),
      }}
    >
      <Title />
      <div style={{ position: "relative", flex: 1, marginTop: 28 }}>
        {SHEETS.map((sheet, index) => (
          <ReportSheet
            key={sheet.label}
            src={sheet.src}
            label={sheet.label}
            index={index}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};
