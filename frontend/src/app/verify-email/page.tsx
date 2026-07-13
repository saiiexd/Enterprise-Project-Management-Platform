'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [error, setError] = useState<string | null>(() => {
    return token ? null : 'Verification token is missing.';
  });
  const [loading, setLoading] = useState(!!token);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!token) return;

    const performVerification = async () => {
      try {
        const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        const res = await fetch(`${apiURL}/auth/verify-email`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ token }),
        });

        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.detail || 'Email verification failed.');
        }

        setSuccess(true);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Verification link expired or invalid.';
        setError(msg);
      } finally {
        setLoading(false);
      }
    };

    performVerification();
  }, [token]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-radial from-slate-900 via-gray-950 to-black px-4 text-white">
      <div className="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-900/60 p-8 backdrop-blur-xl shadow-2xl text-center">
        <h2 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-6">
          Email Verification
        </h2>

        {loading && (
          <div className="flex flex-col items-center gap-4 py-8">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
            <p className="text-sm font-medium text-gray-400">Verifying your account details...</p>
          </div>
        )}

        {!loading && success && (
          <div className="space-y-4">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-950 border border-green-800 text-green-400">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-green-400">Account Verified!</h3>
            <p className="text-sm text-gray-400">Your email has been verified. You can now access all workspace resources.</p>
            <button
              onClick={() => router.push('/login')}
              className="mt-6 w-full rounded-lg bg-indigo-600 hover:bg-indigo-500 py-3 text-sm font-bold text-white transition"
            >
              Sign In to Platform
            </button>
          </div>
        )}

        {!loading && error && (
          <div className="space-y-4">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-950 border border-red-800 text-red-400">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h3 className="text-lg font-bold text-red-400">Verification Failed</h3>
            <p className="text-sm text-gray-400">{error}</p>
            <button
              onClick={() => router.push('/login')}
              className="mt-6 w-full rounded-lg border border-gray-800 bg-gray-950/40 hover:bg-gray-950/80 py-3 text-sm font-semibold text-white transition"
            >
              Back to Login
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
