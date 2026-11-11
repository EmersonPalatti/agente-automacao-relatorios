import type { FC } from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS, DUR, FONTS, SAFE, SCENES, SPRING } from "../theme";

const ITEMS = [
  "Limpar a base",
  "Calcular os mesmos recortes",
  "Montar os gráficos",
  "Escrever o resumo",
] as const;

const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const Title: FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: SPRING });

  return (
    <h1
      style={{
        margin: 0,
        maxWidth: 760,
        fontFamily: FONTS.sans,
        fontSize: 84,
        fontWeight: 800,
        lineHeight: 1.05,
        letterSpacing: -1.4,
        color: COLORS.ink,
        opacity: interpolate(enter, [0, 1], [0, 1], clamp),
        translate: interpolate(enter, [0, 1], ["0px 20px", "0px 0px"], clamp),
      }}
    >
      Toda semana,
      <br />o mesmo ritual:
    </h1>
  );
};

const Clock: FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: SPRING });
  const turn = interpolate(frame, [0, SCENES.S2Pain.duration], [0, 480], clamp);

  return (
    <svg
      width={108}
      height={108}
      viewBox="0 0 64 64"
      aria-hidden
      style={{
        flexShrink: 0,
        marginTop: 6,
        opacity: interpolate(enter, [0, 1], [0, 1], clamp),
      }}
    >
      <circle
        cx="32"
        cy="32"
        r="22"
        fill="none"
        stroke={COLORS.redInk}
        strokeWidth="1.25"
      />
      <line
        x1="32"
        y1="32"
        x2="32"
        y2="15"
        stroke={COLORS.redInk}
        strokeWidth="1.25"
        strokeLinecap="round"
        transform={`rotate(${turn} 32 32)`}
      />
      <circle cx="32" cy="32" r="1.75" fill={COLORS.redInk} />
    </svg>
  );
};

const CheckItem: FC<{ label: string; index: number }> = ({ label, index }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const appearAt = 6 + index * 4;
  const checkAt = 32 + index * 18;
  const shown = spring({ frame, fps, delay: appearAt, config: SPRING });
  const check = spring({ frame, fps, delay: checkAt, config: SPRING });

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 28,
        opacity: interpolate(shown, [0, 1], [0, 1], clamp),
        translate: interpolate(shown, [0, 1], ["0px 18px", "0px 0px"], clamp),
      }}
    >
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: 12,
          border: `2px solid ${check > 0.4 ? COLORS.ink : COLORS.line}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <svg width={30} height={30} viewBox="0 0 32 32" aria-hidden>
          <path
            d="M7 16.5 L13 22.5 L25 9.5"
            fill="none"
            stroke={COLORS.ink}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{
              opacity: interpolate(check, [0, 1], [0, 1], clamp),
              scale: interpolate(check, [0, 1], [0.82, 1], clamp),
            }}
          />
        </svg>
      </div>
      <span
        style={{
          fontFamily: FONTS.sans,
          fontSize: 46,
          fontWeight: 600,
          lineHeight: 1.15,
          color: COLORS.ink,
        }}
      >
        {label}
      </span>
    </div>
  );
};

export const S2Pain: FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [SCENES.S2Pain.duration - DUR.exit, SCENES.S2Pain.duration],
    [1, 0],
    clamp,
  );

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg }}>
      <AbsoluteFill
        style={{
          paddingTop: SAFE.top,
          paddingBottom: SAFE.bottom,
          paddingLeft: SAFE.x,
          paddingRight: SAFE.x,
          opacity,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: 32,
          }}
        >
          <Title />
          <Clock />
        </div>
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            gap: 40,
            paddingBottom: 48,
          }}
        >
          {ITEMS.map((label, index) => (
            <CheckItem key={label} label={label} index={index} />
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
