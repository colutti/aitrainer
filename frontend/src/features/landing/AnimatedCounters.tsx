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

export const AnimatedCounters = () => {
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
    <section className="pt-4 pb-12 bg-secondary/30 backdrop-blur-sm border-y border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, idx) => (
            <div key={idx} className="text-center group">
              <div className="font-display text-4xl md:text-5xl font-extrabold bg-clip-text text-transparent bg-linear-to-r from-primary to-accent group-hover:scale-110 transition-transform duration-300">
                <Counter end={stat.value} suffix={stat.suffix} />
              </div>
              <div className="text-sm font-medium text-text-secondary uppercase tracking-widest">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
