// Curated theme imagery — free-licensed photos from Wikimedia Commons, resized locally.
// This manifest is the single source of truth: the front page draws from `pool` per theme
// and /creditos renders the attribution list. A navy tint overlay (CSS) unifies the set.
//
// Images are SCARCE by design (ADR-004): only the day's top stories carry one, and each
// theme's pool is visually distinct (facades ≠ medical ≠ money/port). "outros" has no pool
// on purpose — a catch-all theme cannot be pictured honestly.

export interface ThemeImage {
  src: string; // under /img/temas/
  title: string;
  author: string;
  license: string;
  page: string; // Commons file page (attribution link)
}

export const THEME_IMAGES: Record<string, ThemeImage[]> = {
  habitacao: [
    {
      src: "/img/temas/habitacao-1.jpg",
      title: "Houses in Praça Luís de Camões, Lisboa",
      author: "Sergio Calleja",
      license: "CC BY-SA 2.0",
      page: "https://commons.wikimedia.org/wiki/File:Houses_in_Pra%C3%A7a_Lu%C3%ADs_de_Cam%C3%B5es_-_Lisbon_-_Apr_2007.jpg",
    },
    {
      src: "/img/temas/habitacao-2.jpg",
      title: "Casas na Ribeira, Porto",
      author: "Sergei Gussev",
      license: "CC BY 2.0",
      page: "https://commons.wikimedia.org/wiki/File:Old_colorful_houses_in_the_Ribeira_neighborhood_of_Porto,_Porto,_Portugal,_January_2023_(52733600792).jpg",
    },
    {
      src: "/img/temas/habitacao-3.jpg",
      title: "Fachadas com varandas, Lisboa",
      author: "Harvey Barrison",
      license: "CC BY-SA 2.0",
      page: "https://commons.wikimedia.org/wiki/File:Lisbon_2015_10_14_0598_(23597133155).jpg",
    },
  ],
  saude: [
    {
      src: "/img/temas/saude-1.jpg",
      title: "Corredor hospitalar",
      author: "W.carter",
      license: "CC0",
      page: "https://commons.wikimedia.org/wiki/File:Corridor_on_the_second_level_-_N%C3%84L_hospital_1.jpg",
    },
    {
      src: "/img/temas/saude-2.jpg",
      title: "Estetoscópio",
      author: "Jacek Halicki",
      license: "CC BY-SA 4.0",
      page: "https://commons.wikimedia.org/wiki/File:2023_Stetoskop.jpg",
    },
  ],
  economia: [
    {
      src: "/img/temas/economia-2.jpg",
      title: "Notas e moedas de euro",
      author: "Avij",
      license: "Domínio público",
      page: "https://commons.wikimedia.org/wiki/File:Euro_coins_and_banknotes.jpg",
    },
    {
      src: "/img/temas/economia-3.jpg",
      title: "Terminal de contentores, Porto de Sines",
      author: "APS — Administração do Porto de Sines",
      license: "CC BY-SA 4.0",
      page: "https://commons.wikimedia.org/wiki/File:PortofSinesAccess.jpg",
    },
  ],
};
