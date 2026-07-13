'use client';

import React from 'react';
import { useRouter } from 'next/navigation';

export default function UnauthorizedPage() {
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center bg-radial from-slate-900 via-gray-950 to-black px-4 text-white">
      <div className="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-900/60 p-8 backdrop-blur-xl shadow-2xl text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-yellow-950 border border-yellow-800 text-yellow-500 mb-6">
          <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>

        <h2 className="text-2xl font-extrabold tracking-tight text-yellow-500 mb-2">
          Access Denied
        </h2>
        <p className="text-sm text-gray-400 mb-6">
          You do not have the required permissions or organization role privileges to access this resource.
        </p>

        <div className="flex gap-4">
          <button
            onClick={() => router.back()}
            className="w-1/2 rounded-lg border border-gray-800 bg-gray-950/40 hover:bg-gray-950/80 py-3 text-sm font-semibold transition"
          >
            Go Back
          </button>
          <button
            onClick={() => router.push('/')}
            className="w-1/2 rounded-lg bg-indigo-600 hover:bg-indigo-500 py-3 text-sm font-bold transition"
          >
            Home Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
