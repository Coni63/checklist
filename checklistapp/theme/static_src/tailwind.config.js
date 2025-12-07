module.exports = {
  content: [
    // templates du projet Django
    "../../../templates/**/*.html",
    "../../../**/templates/**/*.html",

    // si tu as des templates dans app/
    "../../templates/**/*.html",
    "../../**/templates/**/*.html",

    // fichiers JS éventuellement
    "../../../**/*.js",
  ],
  theme: {
    extend: {},
  },
  plugins: [
    //require("daisyui")
  ],
  daisyui: {
    /*
    themes: [
      {
        light: {
          ...require("daisyui/src/theming/themes")["light"],
          primary: "#667eea",
          "primary-focus": "#5568d3",
          secondary: "#764ba2",
          accent: "#4dabf7",
          neutral: "#343a40",
          "base-100": "#ffffff",
          "base-200": "#f1f3f5",
          "base-300": "#e9ecef",
          info: "#4dabf7",
          success: "#51cf66",
          warning: "#ffd93d",
          error: "#ff6b6b",
        },
      },
      "dark",
      "cupcake",
      "corporate",
      "synthwave",
      "retro",
      "cyberpunk",
      "valentine",
      "halloween",
      "garden",
      "forest",
      "aqua",
      "lofi",
      "pastel",
      "fantasy",
      "wireframe",
      "black",
      "luxury",
      "dracula",
    ],
    */
    themes: false
  },
};
