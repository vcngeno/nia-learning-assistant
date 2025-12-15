'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('https://web-production-5e612.up.railway.app/api/v1/auth/parent/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: fullName, email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Registration failed');
      }

      const data = await response.json();
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify({
        email: data.email,
        full_name: data.full_name,
        parent_id: data.parent_id
      }));

      window.location.href = '/dashboard';
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-12">
          <Link href="/" className="inline-block mb-6">
            <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center text-white font-bold text-3xl mx-auto mb-4">
              N
            </div>
            <span className="font-bold text-3xl">Nia</span>
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 mt-6 mb-3">Create Your Account</h1>
          <p className="text-xl text-gray-600">Start your child's learning journey today</p>
        </div>

        <form onSubmit={handleRegister} className="bg-white rounded-2xl border-2 border-gray-200 p-10 space-y-6">
          {error && (
            <div className="bg-red-50 border-2 border-red-200 text-red-700 px-6 py-4 rounded-xl font-semibold text-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block text-lg font-bold text-gray-900 mb-3">Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-5 py-4 border-2 border-gray-300 rounded-xl text-lg focus:border-blue-600 focus:outline-none"
              placeholder="Jane Smith"
              required
            />
          </div>

          <div>
            <label className="block text-lg font-bold text-gray-900 mb-3">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-5 py-4 border-2 border-gray-300 rounded-xl text-lg focus:border-blue-600 focus:outline-none"
              placeholder="you@example.com"
              required
            />
          </div>

          <div>
            <label className="block text-lg font-bold text-gray-900 mb-3">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-5 py-4 border-2 border-gray-300 rounded-xl text-lg focus:border-blue-600 focus:outline-none"
              placeholder="••••••••"
              minLength={8}
              required
            />
            <p className="text-sm text-gray-500 mt-2">Must be at least 8 characters</p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-8 py-5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-xl disabled:opacity-50"
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>

          <div className="text-center pt-4">
            <p className="text-lg text-gray-600">
              Already have an account?{' '}
              <Link href="/login" className="text-blue-600 hover:text-blue-700 font-bold">
                Sign In
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
