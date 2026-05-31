"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { SignInPage } from "@/components/ui/sign-in";

// ── Admin credentials ─────────────────────────────────────────────────────────
const ADMIN_USERNAME = "admin";
const ADMIN_PASSWORD = "TAVSS2026";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSignIn = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    const formData = new FormData(event.currentTarget);
    const username = (formData.get("username") as string)?.trim();
    const password = formData.get("password") as string;

    setTimeout(() => {
      if (username === ADMIN_USERNAME && password === ADMIN_PASSWORD) {
        // ── Connect to Webapp Auth ──────────────────────────────────────────
        // The webapp's proxy.ts expects a cookie 'tavss_auth' with value 'granted'
        document.cookie = "tavss_auth=granted; path=/; max-age=3600; SameSite=Lax";
        
        // Also keep sessionStorage for the Navigation component's state tracking
        sessionStorage.setItem("tavss_auth", "true");
        
        // Redirect to the intended destination or home
        const params = new URLSearchParams(window.location.search);
        const from = params.get("from") || "/";
        router.push(from);
      } else {
        setError("Invalid username or password. Please try again.");
        setLoading(false);
      }
    }, 600);
  };

  const handleResetPassword = () => {
    setError("Contact the project admin to reset your credentials.");
  };

  const handleCreateAccount = () => {
    setError("Account creation is restricted to authorized personnel.");
  };

  return (
    <SignInPage
      title={
        <span className="font-light tracking-tighter text-white">
          Welcome to <span className="font-bold text-red-500">TAVSS</span>
        </span>
      }
      description="Access your workspace and continue your journey with the GECS-Sage classifier."
      heroImageSrc="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=2160&q=80"
      onSignIn={handleSignIn}
      onResetPassword={handleResetPassword}
      onCreateAccount={handleCreateAccount}
      error={error}
      loading={loading}
    />
  );
}
