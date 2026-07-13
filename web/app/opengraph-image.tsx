import { ImageResponse } from "next/og";

// Typographic share card in the site's navy identity — no photos, same sober register.
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "dr-watch — o Diário da República, em linguagem humana";

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "88px",
          background: "linear-gradient(135deg, #1e2a38 0%, #2a5a8c 100%)",
          color: "#ffffff",
        }}
      >
        <div style={{ fontSize: 92, fontWeight: 700 }}>dr-watch</div>
        <div style={{ fontSize: 38, color: "#c6d3e2", marginTop: 12 }}>
          o Diário da República, em linguagem humana
        </div>
        <div style={{ fontSize: 26, color: "#8fa5bd", marginTop: 56, lineHeight: 1.4 }}>
          Cada diploma explicado em linguagem clara, com ligação ao documento oficial e
          verificação automática, todos os dias.
        </div>
      </div>
    ),
    size
  );
}
