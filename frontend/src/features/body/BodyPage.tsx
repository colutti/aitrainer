import { useLocation, useNavigate } from 'react-router-dom';

import { BodyView, type BodyTab } from './components/BodyView';

/**
 * BodyPage component (Container)
 * 
 * Tracks weight, body composition and nutrition.
 * Metabolism data is now consolidated in the main Dashboard.
 */
export default function BodyPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // Determine active tab based on URL
  const activeTab: BodyTab = 
    location.pathname.includes('nutrition') 
      ? 'nutrition' 
      : 'weight';

  const handleTabChange = (tab: BodyTab) => {
    void navigate(`/dashboard/body/${tab}`);
  };
  
  return (
    <section className="mx-auto w-full max-w-[1600px]">
      <BodyView 
        activeTab={activeTab} 
        onTabChange={handleTabChange} 
      />
    </section>
  );
}
