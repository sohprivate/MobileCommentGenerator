import { style } from '@vanilla-extract/css';
import { vars } from '../styles/theme.css';

export const card = style({
  borderRadius: vars.radii.md,
  backgroundColor: vars.colors.surface,
  border: `1px solid ${vars.colors.border}`,
  transition: 'all 0.2s ease',
  cursor: 'pointer',
  display: 'flex',
  flexDirection: 'column',
  padding: vars.spacing[6],
  width: '100%',
  ':hover': {
    borderColor: vars.colors.primary[500],
  },
  selectors: {
    '&:focus-visible': {
      borderColor: vars.colors.primary[500],
      outline: 'none',
      boxShadow: `0 0 0 2px ${vars.colors.primary[500]}, 0 0 0 4px rgba(59, 130, 246, 0.1)`,
    },
    '@media (min-width: 768px)': {
      width: '33.333333%',
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

export const featureItem = style({
  display: 'flex',
  alignItems: 'center',
  marginBottom: vars.spacing[3],
});

export const featureIcon = style({
  width: vars.spacing[5],
  height: vars.spacing[5],
  color: vars.colors.primary[500],
  marginRight: vars.spacing[2],
  flexShrink: 0,
});

export const featureText = style({
  fontSize: vars.fontSizes.sm,
  color: vars.colors.neutral[600],
});