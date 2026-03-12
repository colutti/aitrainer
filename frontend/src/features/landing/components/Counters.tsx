import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

interface CounterProps {
  end: number;
  suffix?: string;
  duration?: number;
}

const Counter = ({ end, suffix = '', duration = 2000 }: CounterProps) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let startTime: number | null = null;
    let animationFrame: number;

    const animate = (timestamp: number) => {
      startTime ??= timestamp;
      const progress = timestamp - startTime;
      const percentage = Math.min(progress / duration, 1);
      
      setCount(Math.floor(end * percentage));

      if (percentage < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => { cancelAnimationFrame(animationFrame); };
  }, [end, duration]);

  return (
    <span>
      {count}
      {suffix}
    </span>
  );
};

export const Counters = () => {
  const { t } = useTranslation();

  const stats = [
    {
      label: t('landing.counters.trainers'),
      value: 6,
      suffix: '',
    },
    {
      label: t('landing.counters.availability'),
      value: 24,
      suffix: '/7',
    },
    {
      label: t('landing.counters.integrations'),
      value: 3,
      suffix: '+',
    },
    {
      label: t('landing.counters.memory'),
      value: 100,
      suffix: '%',
    },
  ];

  return (
    <section className="py-12 border-y border-border bg-dark-bg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, idx) => (
            <div key={idx} className="text-center">
              <div className="font-display text-4xl font-bold text-text-primary mb-2">
                <Counter end={stat.value} suffix={stat.suffix} />
              </div>
              <div className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
