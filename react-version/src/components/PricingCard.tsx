import { Check } from 'lucide-react';
import { clsx } from 'clsx';
import { usePricingStore, type PlanKey } from '../store';
import * as styles from './PricingCard.css';

interface PricingCardProps {
  planKey: PlanKey;
  title: string;
  price: string;
  features: string[];
  className?: string;
}

export function PricingCard({ planKey, title, price, features, className }: PricingCardProps) {
  const { selectedPlan, setSelectedPlan } = usePricingStore();
  const isSelected = selectedPlan === planKey;

  const handleClick = () => {
    setSelectedPlan(planKey);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setSelectedPlan(planKey);
    }
  };

  return (
    <button
      type="button"
      aria-pressed={isSelected}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className={clsx(
        styles.card,
        isSelected && styles.selected,
        className
      )}
    >
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.price}>{price}</p>
      <ul className={styles.featureList}>
        {features.map((feature) => (
          <li key={feature} className={styles.featureItem}>
            <Check className={styles.featureIcon} />
            <span className={styles.featureText}>{feature}</span>
          </li>
        ))}
      </ul>
    </button>
  );
}