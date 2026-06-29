"use client";

import { AppContextProvider } from "./context/AppContext";
import { useIsMobile } from "./hooks/useIsMobile";
import { DesktopLayout } from "./layouts/DesktopLayout";
import { MobileLayout } from "./layouts/MobileLayout";

function AppDispatcher() {
  const { isMobile, isMounted } = useIsMobile();

  if (!isMounted) {
    return <div style={{ minHeight: "100vh", background: "var(--bg)" }} />;
  }

  return isMobile ? <MobileLayout /> : <DesktopLayout />;
}

export default function Page() {
  return (
    <AppContextProvider>
      <AppDispatcher />
    </AppContextProvider>
  );
}
