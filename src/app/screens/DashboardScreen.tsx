import React from 'react';
import { motion } from 'motion/react';
import { StatsSection } from '../components/dashboard/StatsSection';
import { RecentActivity } from '../components/dashboard/RecentActivity';
import { SuggestedBuilders } from '../components/dashboard/SuggestedBuilders';
import { BuildersFlare } from '../components/dashboard/BuildersFlare';
import { QuickActions } from '../components/dashboard/QuickActions';
import { DashboardLayout } from '../components/layout/DashboardLayout';
import { AIAssistant } from '../components/AIAssistant';

interface DashboardScreenProps {
  onLogout?: () => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ onLogout }) => {
  return (
    <DashboardLayout onLogout={onLogout}>
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex flex-col gap-12"
      >
        {/* Top: Stats Grid */}
        <section>
          <StatsSection />
        </section>

        {/* Bottom: Main Grid (70/30) */}
        <div className="grid grid-cols-1 gap-12 xl:grid-cols-[1fr_400px]">
          {/* Left Column (70%) */}
          <div className="flex flex-col gap-12 overflow-hidden">
            <RecentActivity />
            <SuggestedBuilders />
          </div>

          {/* Right Column (30%) */}
          <aside className="flex flex-col gap-12">
            <BuildersFlare />
            <QuickActions />
          </aside>
        </div>
      </motion.div>
      
      {/* Floating AI Assistant */}
      <AIAssistant />
    </DashboardLayout>
  );
};
