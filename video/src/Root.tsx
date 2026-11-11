import React from "react";
import { Composition } from "remotion";
import "./fonts";
import { VIDEO } from "./theme";
import { LinkedInVideo } from "./Video";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="LinkedInVideo"
      component={LinkedInVideo}
      width={VIDEO.width}
      height={VIDEO.height}
      fps={VIDEO.fps}
      durationInFrames={VIDEO.durationInFrames}
    />
  );
};
