import { THEME_LABEL, THEME_ORDER } from "@/lib/db";
import { THEME_IMAGES } from "@/lib/images";

export const metadata = { title: "Créditos de imagem — dr-watch" };

export default function Creditos() {
  return (
    <div className="narrow">
      <h1>Créditos de imagem</h1>
      <p className="subtitle">
        As fotografias do site são ilustrações temáticas — não retratam os diplomas — obtidas
        do Wikimedia Commons sob licenças livres, listadas abaixo com autoria e licença.
      </p>
      {THEME_ORDER.map((t) => (
        <section key={t}>
          <h2 className="theme-header">{THEME_LABEL[t]}</h2>
          <ul className="credit-list">
            {(THEME_IMAGES[t] ?? []).map((img) => (
              <li key={img.src}>
                <a href={img.page}>{img.title}</a> — {img.author} · {img.license}
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
