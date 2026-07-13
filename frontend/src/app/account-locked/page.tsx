'use client';

import React from 'react';
import { useRouter } from 'next/navigation';

export default function AccountLockedPage() {
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-radial from-slate-900 via-gray-950 to-black px-4 text-white">
      <div className="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-900/60 p-8 backdrop-blur-xl shadow-2xl text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-950 border border-red-800 text-red-500 mb-6">
          <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>

        <h2 className="text-2xl font-extrabold tracking-tight text-red-400 mb-2">
          Account Locked
        </h2>
        <p className="text-sm text-gray-400 mb-6">
          For your security, your account has been temporarily locked due to too many failed login attempts.
        </p>

        <div className="rounded-lg bg-gray-950/80 border border-gray-800 p-4 text-sm text-gray-500 text-left mb-6 space-y-2">
          <div className="flex justify-between">
            <span>Lockout Reason:</span>
            <span className="font-semibold text-gray-300">Brute Force Protection</span>
          </div>
          <div className="flex justify-between">
            <span>Duration:</span>
            <span className="font-semibold text-gray-300">15 Minutes</span>
          </div>
        </div>

        <button
          onClick={() => router.push('/login')}
          className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-500 py-3 text-sm font-bold text-white transition"
        >
          Return to Sign In
        </button>
      </div>
    </div>
  );
}
