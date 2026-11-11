import React from "react";
import { FadeIn } from "../components/FadeIn";
import { Chip } from "../components/Chip";
import { SceneFrame } from "../components/SceneFrame";
import { COLORS, DUR, FONTS } from "../theme";

const STACK = ["Python", "LangGraph", "Polars", "DuckDB", "Streamlit"] as const;

export const S8Outro: React.FC = () => {
  return (
    <SceneFrame
      style={{
        justifyContent: "center",
        alignItems: "center",
        gap: 64,
      }}
    >
      <FadeIn>
        <div
          style={{
            fontFamily: FONTS.sans,
            fontWeight: 800,
            fontSize: 76,
            lineHeight: 1.08,
            letterSpacing: -1.5,
            color: COLORS.ink,
            textAlign: "center",
          }}
        >
          Agente de automação
          <br />
          de relatórios
        </div>
      </FadeIn>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: 18,
          width: 760,
        }}
      >
        {STACK.map((name, index) => (
          <FadeIn key={name} delay={10 + index * DUR.stagger} style={{ width: "fit-content" }}>
            <Chip
              bg={COLORS.white}
              ink={COLORS.ink}
              style={{ border: `2px solid ${COLORS.line}`, fontSize: 40, padding: "16px 28px" }}
            >
              {name}
            </Chip>
          </FadeIn>
        ))}
      </div>
      <FadeIn delay={38}>
        <div
          style={{
            fontFamily: FONTS.sans,
            fontWeight: 600,
            fontSize: 40,
            lineHeight: 1.25,
            color: COLORS.ink,
            textAlign: "center",
          }}
        >
          Teste o app → link nos comentários
        </div>
      </FadeIn>
    </SceneFrame>
  );
};
