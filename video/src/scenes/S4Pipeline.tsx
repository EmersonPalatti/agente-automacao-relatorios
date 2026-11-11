import type { CSSProperties, FC } from "react";
import {
  AbsoluteFill,
  interpolate,
  interpolateColors,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS, DUR, EASE_OUT, FONTS, SAFE, SCENES, SPRING } from "../theme";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const DOT = 20;
const PILL_H = 72;
const NODE_TOP = 204;
const NODE_STRIDE = 144;
const RAIL_X = SAFE.x;
const LOOP_X = 620;

const nodeTop = (index: number) => NODE_TOP + index * NODE_STRIDE;
const nodeMid = (index: number) => nodeTop(index) + PILL_H / 2;

type Step = {
  name: string;
  subtitle: string;
  llm: boolean;
  at: number;
};

// Frames locais. analyze fica ativo ~104 frames (144→248).
const STEPS: Step[] = [
  { name: "ingest", subtitle: "CSV · Excel · Parquet · SQL", llm: false, at: 12 },
  { name: "clean", subtitle: "espaços, nulos, colunas vazias", llm: false, at: 45 },
  { name: "profile", subtitle: "estatísticas calculadas", llm: false, at: 78 },
  { name: "plan", subtitle: "escolhe as análises", llm: true, at: 111 },
  { name: "analyze", subtitle: "Python no sandbox", llm: true, at: 144 },
  { name: "write", subtitle: "insights a partir das métricas", llm: true, at: 248 },
  { name: "compile", subtitle: "Markdown + PDF", llm: false, at: 284 },
];

// A linha segura em analyze enquanto o mini-loop roda.
const LINE_FRAMES = [12, 45, 78, 111, 144, 230, 248, 284];
const LINE_AT = [0, 1, 2, 3, 4, 4, 5, 6];

type LoopKind = "text" | "bad" | "good";

const LOOP: { label: string; kind: LoopKind; at: number }[] = [
  { label: "código gerado", kind: "text", at: 150 },
  { label: "sandbox", kind: "text", at: 164 },
  { label: "erro", kind: "bad", at: 174 },
  { label: "retry", kind: "text", at: 192 },
  { label: "métricas", kind: "good", at: 210 },
];

const AGENT_SECONDS = 127;

const formatClock = (totalSeconds: number) => {
  const safe = Math.max(0, Math.min(AGENT_SECONDS, totalSeconds));
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
};

const litAmount = (frame: number, fps: number, at: number) => {
  const raw = spring({ frame, fps, delay: at, config: SPRING });
  return interpolate(raw, [0, 1], [0, 1], clamp);
};

const Header: FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: SPRING });
  const seconds = Math.round(
    interpolate(frame, [0, SCENES.S4Pipeline.duration - 1], [0, AGENT_SECONDS], clamp),
  );

  return (
    <div
      style={{
        position: "absolute",
        top: SAFE.top,
        left: SAFE.x,
        right: SAFE.x,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "baseline",
        opacity: interpolate(enter, [0, 1], [0, 1], clamp),
        translate: interpolate(enter, [0, 1], ["0px 12px", "0px 0px"], clamp),
      }}
    >
      <div
        style={{
          fontFamily: FONTS.sans,
          fontWeight: 600,
          fontSize: 36,
          lineHeight: 1.1,
          letterSpacing: -0.4,
          color: COLORS.ink,
        }}
      >
        Como funciona
      </div>
      <div
        style={{
          fontFamily: FONTS.mono,
          fontWeight: 500,
          fontSize: 40,
          lineHeight: 1,
          letterSpacing: -0.6,
          color: COLORS.ink,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {formatClock(seconds)}
      </div>
    </div>
  );
};

const Rail: FC = () => {
  const frame = useCurrentFrame();
  const top = nodeMid(0);
  const length = nodeMid(STEPS.length - 1) - top;
  const drawn = interpolate(
    frame,
    LINE_FRAMES,
    LINE_AT.map((index) => (index / (STEPS.length - 1)) * length),
    { ...clamp, easing: EASE_OUT },
  );

  return (
    <div
      style={{
        position: "absolute",
        left: RAIL_X + DOT / 2 - 1,
        top,
        width: 2,
        height: length,
        backgroundColor: COLORS.line,
        borderRadius: 1,
      }}
    >
      <div
        style={{
          width: 2,
          height: drawn,
          backgroundColor: COLORS.ink,
          borderRadius: 1,
        }}
      />
    </div>
  );
};

const StepNode: FC<{ step: Step; index: number }> = ({ step, index }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = litAmount(frame, fps, step.at);
  const border = interpolateColors(t, [0, 1], [COLORS.line, COLORS.ink]);
  const nameColor = interpolateColors(
    t,
    [0, 1],
    [COLORS.gray, step.llm ? COLORS.bg : COLORS.ink],
  );
  const fill = step.llm
    ? interpolateColors(t, [0, 1], [COLORS.bg, COLORS.ink])
    : COLORS.bg;
  const dotFill = step.llm ? fill : COLORS.bg;
  const tagColor = interpolateColors(t, [0, 1], [COLORS.gray, COLORS.ink]);
  const tagBorder = interpolateColors(t, [0, 1], [COLORS.line, COLORS.bg]);

  return (
    <div
      style={{
        position: "absolute",
        top: nodeTop(index),
        left: RAIL_X,
        display: "flex",
        alignItems: "flex-start",
        zIndex: 1,
      }}
    >
      <div
        style={{
          width: DOT,
          height: DOT,
          marginTop: (PILL_H - DOT) / 2,
          boxSizing: "border-box",
          borderRadius: 999,
          border: `2px solid ${border}`,
          backgroundColor: dotFill,
          flexShrink: 0,
        }}
      />
      <div style={{ marginLeft: 18 }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            height: PILL_H,
            padding: "0 22px",
            boxSizing: "border-box",
            borderRadius: 999,
            border: `2px solid ${border}`,
            backgroundColor: fill,
          }}
        >
          <span
            style={{
              fontFamily: FONTS.mono,
              fontWeight: 700,
              fontSize: 36,
              lineHeight: 1,
              color: nameColor,
              whiteSpace: "nowrap",
            }}
          >
            {step.name}
          </span>
          {step.llm ? (
            <span
              style={{
                fontFamily: FONTS.mono,
                fontWeight: 700,
                fontSize: 30,
                lineHeight: 1,
                letterSpacing: 0.4,
                color: tagColor,
                backgroundColor: COLORS.bg,
                border: `2px solid ${tagBorder}`,
                borderRadius: 999,
                padding: "4px 8px",
              }}
            >
              LLM
            </span>
          ) : null}
        </div>
        <div
          style={{
            marginTop: 8,
            fontFamily: FONTS.sans,
            fontWeight: 400,
            fontSize: 30,
            lineHeight: 1.15,
            color: COLORS.gray,
            whiteSpace: "nowrap",
            opacity: t,
            translate: interpolate(t, [0, 1], ["0px 8px", "0px 0px"], clamp),
          }}
        >
          {step.subtitle}
        </div>
      </div>
    </div>
  );
};

const loopText: CSSProperties = {
  fontFamily: FONTS.sans,
  fontWeight: 600,
  fontSize: 36,
  lineHeight: 1.1,
  color: COLORS.ink,
  whiteSpace: "nowrap",
};

const LoopMark: FC<{ kind: Exclude<LoopKind, "text"> }> = ({ kind }) => {
  const color = kind === "bad" ? COLORS.redInk : COLORS.greenInk;
  const path = kind === "bad" ? "M7 7 L19 19 M19 7 L7 19" : "M5 14 L11 20 L21 7";
  return (
    <svg width={28} height={28} viewBox="0 0 26 26" aria-hidden>
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth={2.4}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

const LoopStep: FC<{ label: string; kind: LoopKind; at: number; first: boolean }> = ({
  label,
  kind,
  at,
  first,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = litAmount(frame, fps, at);
  const chip: CSSProperties =
    kind === "text"
      ? loopText
      : {
          ...loopText,
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          padding: "8px 16px 8px 12px",
          borderRadius: 999,
          backgroundColor: kind === "bad" ? COLORS.redBg : COLORS.greenBg,
          color: kind === "bad" ? COLORS.redInk : COLORS.greenInk,
        };

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
      {first ? null : (
        <div
          style={{
            width: 2,
            height: 18,
            margin: "10px 0 10px 16px",
            backgroundColor: COLORS.gray,
            opacity: t,
          }}
        />
      )}
      <div
        style={{
          opacity: t,
          translate: interpolate(t, [0, 1], ["0px 8px", "0px 0px"], clamp),
        }}
      >
        <div style={chip}>
          {kind === "text" ? null : <LoopMark kind={kind} />}
          {label}
        </div>
      </div>
    </div>
  );
};

const AnalyzeLoop: FC = () => {
  return (
    <div
      style={{
        position: "absolute",
        left: LOOP_X,
        top: nodeTop(4) + 8,
        zIndex: 1,
      }}
    >
      {LOOP.map((item, index) => (
        <LoopStep
          key={item.label}
          label={item.label}
          kind={item.kind}
          at={item.at}
          first={index === 0}
        />
      ))}
    </div>
  );
};

export const S4Pipeline: FC = () => {
  const frame = useCurrentFrame();
  const exit = interpolate(
    frame,
    [SCENES.S4Pipeline.duration - DUR.exit, SCENES.S4Pipeline.duration],
    [1, 0],
    clamp,
  );

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg }}>
      <AbsoluteFill style={{ opacity: exit }}>
        <Header />
        <Rail />
        {STEPS.map((step, index) => (
          <StepNode key={step.name} step={step} index={index} />
        ))}
        <AnalyzeLoop />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
