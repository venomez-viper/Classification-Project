"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import MLOpsDashboard from "@/components/MLOpsDashboard";

export default function MLPage() {
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    const hasCookie = document.cookie.split(';').some((item) => item.trim().startsWith('tavss_auth=granted'));
    const hasSession = sessionStorage.getItem("tavss_auth") === "true";
    
    if (!hasCookie && !hasSession) {
      router.push("/login?from=/ml");
    } else {
      setIsAuthorized(true);
    }
  }, [router]);

  if (!isAuthorized) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-red-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return <MLOpsDashboard />;
}
