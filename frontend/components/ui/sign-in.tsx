"use client";

import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

// --- TYPE DEFINITIONS ---

interface SignInPageProps {
  title?: React.ReactNode;
  description?: React.ReactNode;
  heroImageSrc?: string;
  onSignIn?: (event: React.FormEvent<HTMLFormElement>) => void;
  onResetPassword?: () => void;
  onCreateAccount?: () => void;
  error?: string;
  loading?: boolean;
}

// --- SUB-COMPONENTS ---

const GlassInputWrapper = ({ children }: { children: React.ReactNode }) => (
  <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm transition-colors focus-within:border-red-400/70 focus-within:bg-red-500/10">
    {children}
  </div>
);

// --- MAIN COMPONENT ---

export const SignInPage: React.FC<SignInPageProps> = ({
  title = <span className="font-light text-white tracking-tighter">Welcome</span>,
  description = "Access your account and continue your journey with us",
  heroImageSrc,
  onSignIn,
  onResetPassword,
  onCreateAccount,
  error = "",
  loading = false,
}) => {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="h-[100dvh] flex flex-col md:flex-row font-geist w-[100dvw] bg-black text-white overflow-hidden">
      {/* Left column: sign-in form */}
      <section className="flex-1 flex items-center justify-center p-8 overflow-y-auto">
        <div className="w-full max-w-md">
          <div className="flex flex-col gap-6">
            <h1 className="animate-element animate-delay-100 text-4xl md:text-5xl font-semibold leading-tight">{title}</h1>
            <p className="animate-element animate-delay-200 text-white/60">{description}</p>

            <form className="space-y-5" onSubmit={onSignIn}>

              <div className="animate-element animate-delay-300">
                <label className="block text-sm font-medium text-white/60 mb-2">Username</label>
                <GlassInputWrapper>
                  <input
                    name="username"
                    type="text"
                    placeholder="Enter your username"
                    required
                    autoComplete="username"
                    className="w-full bg-transparent text-sm p-4 rounded-2xl focus:outline-none text-white placeholder-white/30"
                  />
                </GlassInputWrapper>
              </div>

              <div className="animate-element animate-delay-400">
                <label className="block text-sm font-medium text-white/60 mb-2">Password</label>
                <GlassInputWrapper>
                  <div className="flex items-center gap-2 px-4">
                    <input
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Enter your password"
                      required
                      autoComplete="current-password"
                      className="flex-1 bg-transparent text-sm py-4 focus:outline-none text-white placeholder-white/30 min-w-0"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      style={{ overflow: 'visible' }}
                      className="flex-shrink-0 flex items-center justify-center text-white/50 hover:text-white transition-colors"
                    >
                      {showPassword
                        ? <EyeOff className="w-4 h-4" />
                        : <Eye className="w-4 h-4" />
                      }
                    </button>
                  </div>
                </GlassInputWrapper>
              </div>

              <div className="animate-element animate-delay-500 flex items-center justify-between text-sm">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    name="rememberMe"
                    className="rounded border-white/20 bg-black/50 accent-red-500 h-4 w-4"
                  />
                  <span className="text-white/90">Keep me signed in</span>
                </label>
                <button
                  type="button"
                  onClick={onResetPassword}
                  className="hover:underline text-red-400 transition-colors bg-transparent border-none p-0 cursor-pointer"
                >
                  Forgot password?
                </button>
              </div>

              {/* Error message */}
              {error && (
                <div className="rounded-xl border border-red-500/30 bg-red-950/40 px-4 py-3 text-sm text-red-400 animate-in fade-in slide-in-from-top-1">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="animate-element animate-delay-600 w-full rounded-2xl bg-red-600 py-4 font-medium text-white hover:bg-red-700 transition-colors shadow-[0_0_20px_rgba(220,38,38,0.3)] disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Authenticating...
                  </>
                ) : "Sign In"}
              </button>
            </form>

            <p className="animate-element animate-delay-700 text-center text-sm text-white/60">
              Don&apos;t have an account?{' '}
              <button
                type="button"
                onClick={onCreateAccount}
                className="text-red-400 hover:underline transition-colors bg-transparent border-none p-0 cursor-pointer font-medium"
              >
                Create Account
              </button>
            </p>
          </div>
        </div>
      </section>

      {/* Right column: hero image */}
      {heroImageSrc && (
        <section className="hidden md:block flex-1 relative p-4">
          <div
            className="animate-slide-right animate-delay-300 absolute inset-4 rounded-3xl bg-cover bg-center border border-white/10 shadow-2xl overflow-hidden"
            style={{ backgroundImage: `url(${heroImageSrc})` }}
          >
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
          </div>
        </section>
      )}
    </div>
  );
};
