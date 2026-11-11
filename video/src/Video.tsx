import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { S1Hook } from "./scenes/S1Hook";
import { S2Pain } from "./scenes/S2Pain";
import { S3Question } from "./scenes/S3Question";
import { S4Pipeline } from "./scenes/S4Pipeline";
import { S5Report } from "./scenes/S5Report";
import { S6Metrics } from "./scenes/S6Metrics";
import { S7Trust } from "./scenes/S7Trust";
import { S8Outro } from "./scenes/S8Outro";
import { COLORS, SCENES } from "./theme";

export const LinkedInVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg }}>
      <Sequence from={SCENES.S1Hook.from} durationInFrames={SCENES.S1Hook.duration}>
        <S1Hook />
      </Sequence>
      <Sequence from={SCENES.S2Pain.from} durationInFrames={SCENES.S2Pain.duration}>
        <S2Pain />
      </Sequence>
      <Sequence from={SCENES.S3Question.from} durationInFrames={SCENES.S3Question.duration}>
        <S3Question />
      </Sequence>
      <Sequence from={SCENES.S4Pipeline.from} durationInFrames={SCENES.S4Pipeline.duration}>
        <S4Pipeline />
      </Sequence>
      <Sequence from={SCENES.S5Report.from} durationInFrames={SCENES.S5Report.duration}>
        <S5Report />
      </Sequence>
      <Sequence from={SCENES.S6Metrics.from} durationInFrames={SCENES.S6Metrics.duration}>
        <S6Metrics />
      </Sequence>
      <Sequence from={SCENES.S7Trust.from} durationInFrames={SCENES.S7Trust.duration}>
        <S7Trust />
      </Sequence>
      <Sequence from={SCENES.S8Outro.from} durationInFrames={SCENES.S8Outro.duration}>
        <S8Outro />
      </Sequence>
    </AbsoluteFill>
  );
};
