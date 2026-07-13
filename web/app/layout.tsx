import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "dr-watch — o Diário da República, em linguagem humana",
  description:
    "Resumo diário da Série I do Diário da República: cada diploma explicado em linguagem clara, com ligação ao documento oficial e verificação automática.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt">
      <body>
        <header className="site-header">
          <div className="inner">
            <a className="brand" href="/">
              dr-watch
              <small>o Diário da República, em linguagem humana</small>
            </a>
            <nav>
              <a href="/">Hoje</a>
              <a href="/arquivo">Arquivo</a>
              <a href="/precisao">Precisão</a>
            </nav>
          </div>
        </header>
        <main>{children}</main>
        <footer className="site-footer">
          Resumos gerados automaticamente e verificados por regras determinísticas; em caso de
          dúvida, prevalece sempre o documento oficial, ligado em cada entrada. As imagens são
          ilustrações temáticas (<a href="/creditos">créditos</a>), não retratos dos diplomas.
          Fonte: <a href="https://diariodarepublica.pt">Diário da República</a> ·{" "}
          <a href="https://github.com/diogogs/dr-watch">Como funciona (código aberto)</a> · Um
          projeto de <a href="https://diogogs.github.io">Diogo Guimarães Silva</a>.
        </footer>
      </body>
    </html>
  );
}
