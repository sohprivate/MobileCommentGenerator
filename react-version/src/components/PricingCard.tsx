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
    <div
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className={clsx(
        styles.card,
        isSelected && styles.selected,
        'flex flex-col p-6 w-full md:w-1/3',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
        isSelected && 'ring-2 ring-offset-2 ring-primary-500',
        className
      )}
    >
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.price}>{price}</p>
      <ul className={styles.featureList}>
        {features.map((feature, index) => (
          <li key={index} className="flex items-center mb-3">
            <Check className="w-5 h-5 text-primary-500 mr-2 flex-shrink-0" />
            <span className="text-sm text-gray-600 dark:text-gray-300">{feature}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}