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
  plugins: [require("daisyui")],
};
