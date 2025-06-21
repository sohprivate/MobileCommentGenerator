import { style } from '@vanilla-extract/css';
import { vars } from '../styles/theme.css';

export const card = style({
  borderRadius: vars.radii.md,
  backgroundColor: vars.colors.surface,
  border: `1px solid ${vars.colors.border}`,
  transition: 'all 0.2s ease',
  cursor: 'pointer',
  ':hover': {
    borderColor: vars.colors.primary[500],
  },
  selectors: {
    '&:focus-visible': {
      borderColor: vars.colors.primary[500],
    },
  },
});

export const selected = style({
  borderColor: vars.colors.primary[500],
  boxShadow: `0 0 0 1px ${vars.colors.primary[500]}`,
});

export const title = style({
  fontSize: vars.fontSizes['2xl'],
  fontWeight: 600,
  marginBottom: vars.spacing[2],
});

export const price = style({
  fontSize: vars.fontSizes['3xl'],
  fontWeight: 700,
  marginBottom: vars.spacing[4],
});

export const featureList = style({
  listStyle: 'none',
  padding: 0,
  margin: 0,
});