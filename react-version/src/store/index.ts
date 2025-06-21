import { create } from 'zustand';

export type PlanKey = 'basic' | 'pro' | 'enterprise';

interface PricingState {
  selectedPlan: PlanKey;
  setSelectedPlan: (plan: PlanKey) => void;
}

export const usePricingStore = create<PricingState>((set) => ({
  selectedPlan: 'basic',
  setSelectedPlan: (plan) => set({ selectedPlan: plan }),
}));