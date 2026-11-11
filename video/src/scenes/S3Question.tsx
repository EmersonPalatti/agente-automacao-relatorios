import type { FC } from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { COLORS, DUR, FONTS, SAFE, SCENES, SPRING } from "../theme";

const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const LIFT_AT = 16;
const DROP_AT = 34;
const LIFT_PX = 300;

const Question: FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: SPRING });
  const lift = spring({ frame, fps, delay: LIFT_AT, config: SPRING });

  return (
    <h1
      style={{
        margin: 0,
        fontFamily: FONTS.sans,
        fontSize: 84,
        fontWeight: 800,
        lineHeight: 1.06,
        letterSpacing: -1.4,
        textAlign: "center",
        color: COLORS.ink,
        opacity: interpolate(enter, [0, 1], [0, 1], clamp),
        translate: interpolate(
          lift,
          [0, 1],
          [`0px ${LIFT_PX}px`, "0px 0px"],
          clamp,
        ),
      }}
    >
      E se um agente
      <br />
      fizesse isso?
    </h1>
  );
};

const CsvFile: FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const drop = spring({ frame, fps, delay: DROP_AT, config: SPRING });

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 28,
        opacity: interpolate(drop, [0, 1], [0, 1], clamp),
        translate: interpolate(drop, [0, 1], ["0px -220px", "0px 0px"], clamp),
      }}
    >
      <svg width={248} height={296} viewBox="0 0 188 224" aria-hidden>
        <path
          d="M28 16 H118 L164 62 V208 H28 Z"
          fill={COLORS.white}
          stroke={COLORS.ink}
          strokeWidth="1.75"
          strokeLinejoin="round"
        />
        <path
          d="M118 16 L118 62 L164 62 Z"
          fill={COLORS.line}
          stroke={COLORS.ink}
          strokeWidth="1.75"
          strokeLinejoin="round"
        />
        <line
          x1="92"
          y1="92"
          x2="92"
          y2="184"
          stroke={COLORS.gray}
          strokeWidth="1.25"
        />
        <line
          x1="50"
          y1="104"
          x2="142"
          y2="104"
          stroke={COLORS.ink}
          strokeWidth="1.75"
        />
        <line
          x1="50"
          y1="130"
          x2="142"
          y2="130"
          stroke={COLORS.gray}
          strokeWidth="1.25"
        />
        <line
          x1="50"
          y1="156"
          x2="142"
          y2="156"
          stroke={COLORS.gray}
          strokeWidth="1.25"
        />
        <line
          x1="50"
          y1="182"
          x2="142"
          y2="182"
          stroke={COLORS.gray}
          strokeWidth="1.25"
        />
      </svg>
      <div
        style={{
          fontFamily: FONTS.mono,
          fontSize: 40,
          fontWeight: 500,
          letterSpacing: -0.4,
          color: COLORS.ink,
        }}
      >
        pedidos.csv
      </div>
    </div>
  );
};

export const S3Question: FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [SCENES.S3Question.duration - DUR.exit, SCENES.S3Question.duration],
    [1, 0],
    clamp,
  );

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg }}>
      <AbsoluteFill style={{ opacity }}>
        <div
          style={{
            position: "absolute",
            left: SAFE.x,
            right: SAFE.x,
            top: 280,
          }}
        >
          <Question />
        </div>
        <div
          style={{
            position: "absolute",
            left: SAFE.x,
            right: SAFE.x,
            top: 560,
            display: "flex",
            justifyContent: "center",
          }}
        >
          <CsvFile />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
