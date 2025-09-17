import {themes as prismThemes} from 'prism-react-renderer';

const config = {
  title: 'Shekina',
  tagline: 'Dinosaurs are cool',
  favicon: 'img/favicon.ico',
  url: 'https://your-docusaurus-site.example.com',
  baseUrl: '/',
  organizationName: 'facebook',
  projectName: 'docusaurus',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  i18n: { defaultLocale: 'en', locales: ['en'] },
  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl:
            'https://github.com/facebook/docusaurus/tree/main/packages/create-docusaurus/templates/shared/',
        },
        blog: {
          showReadingTime: true,
          feedOptions: { type: ['rss', 'atom'], xslt: true },
          editUrl:
            'https://github.com/facebook/docusaurus/tree/main/packages/create-docusaurus/templates/shared/',
        },
        theme: { customCss: require.resolve('./src/css/custom.css') },
      },
    ],
  ],
  themes: ['@docusaurus/theme-mermaid'],
  markdown: { mermaid: true },
  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    navbar: {
      title: 'Shekina',
      logo: {
        alt: 'Shekina Logo',
        src: 'img/logo.svg',
      },
      items: [
        {to: '/docs/index', label: 'Inicio', position: 'left'},
        {to: '/docs/concepto/index', label: 'Concepto', position: 'left'},
        {to: '/docs/diseño/index', label: 'Diseño', position: 'left'},
        {to: '/docs/formacion/index', label: 'Formación', position: 'left'},
        {to: '/docs/nacimiento/index', label: 'Nacimiento', position: 'left'}
      ]
    },
    footer: {
      style: 'dark',
      links: [],
      copyright: `Copyright © ${new Date().getFullYear()} Shekina, reinventando el infinito.`
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['mermaid']
    },
    mermaid: {
      theme: { light: 'neutral', dark: 'forest' }
    }
  }
};

export default config;
