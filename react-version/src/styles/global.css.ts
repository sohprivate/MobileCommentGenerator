import { globalStyle } from '@vanilla-extract/css';
import { vars, themeClass } from './theme.css';

globalStyle(':root', {
  fontFamily: 'system-ui, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif',
  lineHeight: 1.6,
  fontWeight: 400,
  colorScheme: 'light',
  color: vars.colors.text,
  backgroundColor: vars.colors.bg,
  fontSynthesis: 'none',
  textRendering: 'optimizeLegibility',
  WebkitFontSmoothing: 'antialiased',
  MozOsxFontSmoothing: 'grayscale',
});

globalStyle('html.dark', {
  colorScheme: 'dark',
});

globalStyle(`html.dark .${themeClass}`, {
  vars: {
    colors: {
      ...vars.colors,
      text: '#f3f4f6',
      bg: '#111827',
      surface: '#1f2937',
      border: '#374151',
    },
  },
});

globalStyle('*', {
  boxSizing: 'border-box',
});

globalStyle('body', {
  margin: 0,
  minWidth: '320px',
  minHeight: '100vh',
  backgroundColor: vars.colors.bg,
});

globalStyle('::-webkit-scrollbar', {
  width: '6px',
});

globalStyle('::-webkit-scrollbar-track', {
  background: '#f1f5f9',
});

globalStyle('html.dark ::-webkit-scrollbar-track', {
  background: '#1f2937',
});

globalStyle('::-webkit-scrollbar-thumb', {
  background: '#cbd5e1',
  borderRadius: '3px',
});

globalStyle('html.dark ::-webkit-scrollbar-thumb', {
  background: '#4b5563',
});

globalStyle('::-webkit-scrollbar-thumb:hover', {
  background: '#94a3b8',
});

globalStyle('html.dark ::-webkit-scrollbar-thumb:hover', {
  background: '#6b7280',
});