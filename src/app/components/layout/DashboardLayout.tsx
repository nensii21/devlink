import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { motion } from 'motion/react';

interface DashboardLayoutProps {
  children: React.ReactNode;
  onLogout?: () => void;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children, onLogout }) => {
  return (
    <div className="flex min-h-screen w-full bg-background selection:bg-primary/10 selection:text-primary antialiased">
      {/* Sidebar - Fixed on desktop */}
      <div className="hidden lg:block">
        <Sidebar onLogout={onLogout} />
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col lg:pl-[280px]">
        {/* Header - Sticky */}
        <Header />

        {/* Content Area */}
        <main className="flex-1">
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="mx-auto w-full max-w-[1600px] p-6 lg:p-10"
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
};
