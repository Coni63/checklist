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
  safelist: [
    // ROUGE - Erreurs
    'bg-red-50', 'bg-red-100', 'bg-red-200', 'bg-red-300', 'bg-red-400', 
    'bg-red-500', 'bg-red-600', 'bg-red-700', 'bg-red-800', 'bg-red-900', 'bg-red-950',
    'text-red-50', 'text-red-100', 'text-red-200', 'text-red-300', 'text-red-400',
    'text-red-500', 'text-red-600', 'text-red-700', 'text-red-800', 'text-red-900', 'text-red-950',
    'border-red-50', 'border-red-100', 'border-red-200', 'border-red-300', 'border-red-400',
    'border-red-500', 'border-red-600', 'border-red-700', 'border-red-800', 'border-red-900', 'border-red-950',
    
    // VERT - Succès
    'bg-green-50', 'bg-green-100', 'bg-green-200', 'bg-green-300', 'bg-green-400',
    'bg-green-500', 'bg-green-600', 'bg-green-700', 'bg-green-800', 'bg-green-900', 'bg-green-950',
    'text-green-50', 'text-green-100', 'text-green-200', 'text-green-300', 'text-green-400',
    'text-green-500', 'text-green-600', 'text-green-700', 'text-green-800', 'text-green-900', 'text-green-950',
    'border-green-50', 'border-green-100', 'border-green-200', 'border-green-300', 'border-green-400',
    'border-green-500', 'border-green-600', 'border-green-700', 'border-green-800', 'border-green-900', 'border-green-950',
    
    // JAUNE - Warnings
    'bg-yellow-50', 'bg-yellow-100', 'bg-yellow-200', 'bg-yellow-300', 'bg-yellow-400',
    'bg-yellow-500', 'bg-yellow-600', 'bg-yellow-700', 'bg-yellow-800', 'bg-yellow-900', 'bg-yellow-950',
    'text-yellow-50', 'text-yellow-100', 'text-yellow-200', 'text-yellow-300', 'text-yellow-400',
    'text-yellow-500', 'text-yellow-600', 'text-yellow-700', 'text-yellow-800', 'text-yellow-900', 'text-yellow-950',
    'border-yellow-50', 'border-yellow-100', 'border-yellow-200', 'border-yellow-300', 'border-yellow-400',
    'border-yellow-500', 'border-yellow-600', 'border-yellow-700', 'border-yellow-800', 'border-yellow-900', 'border-yellow-950',
    
    // BLEU - Info
    'bg-blue-50', 'bg-blue-100', 'bg-blue-200', 'bg-blue-300', 'bg-blue-400',
    'bg-blue-500', 'bg-blue-600', 'bg-blue-700', 'bg-blue-800', 'bg-blue-900', 'bg-blue-950',
    'text-blue-50', 'text-blue-100', 'text-blue-200', 'text-blue-300', 'text-blue-400',
    'text-blue-500', 'text-blue-600', 'text-blue-700', 'text-blue-800', 'text-blue-900', 'text-blue-950',
    'border-blue-50', 'border-blue-100', 'border-blue-200', 'border-blue-300', 'border-blue-400',
    'border-blue-500', 'border-blue-600', 'border-blue-700', 'border-blue-800', 'border-blue-900', 'border-blue-950',
    
    // ESPACEMENTS - Padding
    'p-0', 'p-1', 'p-2', 'p-3', 'p-4', 'p-5', 'p-6', 'p-7', 'p-8', 'p-9', 'p-10',
    'px-0', 'px-1', 'px-2', 'px-3', 'px-4', 'px-5', 'px-6', 'px-7', 'px-8', 'px-9', 'px-10',
    'py-0', 'py-1', 'py-2', 'py-3', 'py-4', 'py-5', 'py-6', 'py-7', 'py-8', 'py-9', 'py-10',
    'pt-0', 'pt-1', 'pt-2', 'pt-3', 'pt-4', 'pt-5', 'pt-6', 'pt-7', 'pt-8', 'pt-9', 'pt-10',
    'pb-0', 'pb-1', 'pb-2', 'pb-3', 'pb-4', 'pb-5', 'pb-6', 'pb-7', 'pb-8', 'pb-9', 'pb-10',
    'pl-0', 'pl-1', 'pl-2', 'pl-3', 'pl-4', 'pl-5', 'pl-6', 'pl-7', 'pl-8', 'pl-9', 'pl-10',
    'pr-0', 'pr-1', 'pr-2', 'pr-3', 'pr-4', 'pr-5', 'pr-6', 'pr-7', 'pr-8', 'pr-9', 'pr-10',
    
    // ESPACEMENTS - Margin
    'm-0', 'm-1', 'm-2', 'm-3', 'm-4', 'm-5', 'm-6', 'm-7', 'm-8', 'm-9', 'm-10',
    'mx-0', 'mx-1', 'mx-2', 'mx-3', 'mx-4', 'mx-5', 'mx-6', 'mx-7', 'mx-8', 'mx-9', 'mx-10',
    'my-0', 'my-1', 'my-2', 'my-3', 'my-4', 'my-5', 'my-6', 'my-7', 'my-8', 'my-9', 'my-10',
    'mt-0', 'mt-1', 'mt-2', 'mt-3', 'mt-4', 'mt-5', 'mt-6', 'mt-7', 'mt-8', 'mt-9', 'mt-10',
    'mb-0', 'mb-1', 'mb-2', 'mb-3', 'mb-4', 'mb-5', 'mb-6', 'mb-7', 'mb-8', 'mb-9', 'mb-10',
    'ml-0', 'ml-1', 'ml-2', 'ml-3', 'ml-4', 'ml-5', 'ml-6', 'ml-7', 'ml-8', 'ml-9', 'ml-10',
    'mr-0', 'mr-1', 'mr-2', 'mr-3', 'mr-4', 'mr-5', 'mr-6', 'mr-7', 'mr-8', 'mr-9', 'mr-10',
    
    // TEXTE
    'text-xs', 'text-sm', 'text-base', 'text-lg', 'text-xl', 'text-2xl',
    'font-normal', 'font-medium', 'font-semibold', 'font-bold',
    'italic', 'not-italic',
    'uppercase', 'lowercase', 'capitalize',
    'text-left', 'text-center', 'text-right',
    
    // BORDURES
    'border', 'border-0', 'border-2', 'border-4', 'border-8',
    'border-t', 'border-r', 'border-b', 'border-l',
    'rounded', 'rounded-sm', 'rounded-md', 'rounded-lg', 'rounded-xl', 'rounded-2xl', 'rounded-full',
    'rounded-t', 'rounded-r', 'rounded-b', 'rounded-l',
    'rounded-t-none', 'rounded-r-none', 'rounded-b-none', 'rounded-l-none',
    
    // OMBRES
    'shadow', 'shadow-sm', 'shadow-md', 'shadow-lg', 'shadow-xl', 'shadow-2xl',
    'shadow-none',
    
    // DISPLAY & LAYOUT
    'block', 'inline-block', 'inline', 'flex', 'inline-flex', 'grid', 'hidden',
    'w-full', 'w-auto', 'w-1/2', 'w-1/3', 'w-2/3', 'w-1/4', 'w-3/4',
    'h-full', 'h-auto',
    'max-w-xs', 'max-w-sm', 'max-w-md', 'max-w-lg', 'max-w-xl', 'max-w-2xl',
    
    // FLEXBOX
    'flex-row', 'flex-col', 'flex-wrap', 'flex-nowrap',
    'items-start', 'items-center', 'items-end', 'items-stretch',
    'justify-start', 'justify-center', 'justify-end', 'justify-between',
    'gap-1', 'gap-2', 'gap-3', 'gap-4', 'gap-5', 'gap-6',
    
    // DIVERS
    'alert',
    'relative', 'absolute', 'fixed', 'sticky',
    'overflow-hidden', 'overflow-auto', 'overflow-scroll',
    'cursor-pointer', 'pointer-events-none',
    'select-none', 'select-text', 'select-all',
  ]
};
