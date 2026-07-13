// Curated theme imagery — free-licensed photos from Wikimedia Commons, resized locally.
// This manifest is the single source of truth: the front page draws from `pool` per theme
// and /creditos renders the attribution list. A navy tint overlay (CSS) unifies the set.

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
    {
      src: "/img/temas/saude-3.jpg",
      title: "Urgência do Hospital de Santa Maria, Lisboa",
      author: "Draceane",
      license: "CC BY-SA 4.0",
      page: "https://commons.wikimedia.org/wiki/File:Hospital_de_Santa_Maria,_Lisboa,_2016_(02).jpg",
    },
  ],
  economia: [
    {
      src: "/img/temas/economia-1.jpg",
      title: "Vista aérea da Baixa de Lisboa",
      author: "Hugo Schneider",
      license: "CC BY 2.0",
      page: "https://commons.wikimedia.org/wiki/File:Aerial_view_of_Augusta_Street,_Lisbon_(50644280948).jpg",
    },
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
    {
      src: "/img/temas/economia-4.jpg",
      title: "Arco da Rua Augusta, Lisboa",
      author: "Dale Cruse",
      license: "CC BY 4.0",
      page: "https://commons.wikimedia.org/wiki/File:Arco_da_Rua_Augusta_and_Pra%C3%A7a_do_Com%C3%A9rcio,_Lisbon_(54725640463).jpg",
    },
  ],
  outros: [
    {
      src: "/img/temas/outros-1.jpg",
      title: "Palácio de São Bento (Assembleia da República)",
      author: "Alvesgaspar",
      license: "CC BY-SA 3.0",
      page: "https://commons.wikimedia.org/wiki/File:Parlamento_April_2009-1a.jpg",
    },
    {
      src: "/img/temas/outros-2.jpg",
      title: "Palácio de São Bento, fachada",
      author: "Felix König",
      license: "CC BY 3.0",
      page: "https://commons.wikimedia.org/wiki/File:Pal%C3%A1cio_de_S%C3%A3o_Bento_Lissabon_September_2014.jpg",
    },
    {
      src: "/img/temas/outros-3.jpg",
      title: "O Palácio de São Bento visto do bairro",
      author: "Lacobrigo",
      license: "CC BY-SA 4.0",
      page: "https://commons.wikimedia.org/wiki/File:Pal%C3%A1cio_de_S%C3%A3o_Bento_3.jpg",
    },
  ],
};
