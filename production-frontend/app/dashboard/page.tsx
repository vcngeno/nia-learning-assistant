'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface Child {
  id: number;
  first_name: string;
  nickname: string | null;
  grade_level: string;
}

export default function DashboardPage() {
  const [user, setUser] = useState<any>(null);
  const [children, setChildren] = useState<Child[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = '/login';
      return;
    }

    try {
      const userStr = localStorage.getItem('user');
      if (userStr) setUser(JSON.parse(userStr));

      const response = await fetch('https://web-production-5e612.up.railway.app/api/v1/children/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setChildren(data);
      }
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl font-semibold">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="border-b">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Nia</h1>
          <button
            onClick={handleLogout}
            className="px-6 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg font-semibold"
          >
            Sign Out
          </button>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="mb-12">
          <h2 className="text-4xl font-bold mb-2">Welcome, {user?.full_name}</h2>
          <p className="text-xl text-gray-600">Manage your students</p>
        </div>

        <div className="grid grid-cols-3 gap-6 mb-12">
          <div className="bg-gray-50 rounded-xl p-8 border-2">
            <div className="text-sm text-gray-600 mb-2">Students</div>
            <div className="text-5xl font-bold">{children.length}</div>
          </div>
          <div className="bg-gray-50 rounded-xl p-8 border-2">
            <div className="text-sm text-gray-600 mb-2">Sessions</div>
            <div className="text-5xl font-bold">0</div>
          </div>
          <div className="bg-gray-50 rounded-xl p-8 border-2">
            <div className="text-sm text-gray-600 mb-2">This Week</div>
            <div className="text-5xl font-bold">0h</div>
          </div>
        </div>

        <div className="flex items-center justify-between mb-8">
          <h3 className="text-3xl font-bold">Your Students</h3>
          <Link
            href="/children/add"
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-lg"
          >
            Add Student
          </Link>
        </div>

        {children.length === 0 ? (
          <div className="bg-gray-50 rounded-2xl p-20 text-center border-2">
            <div className="text-8xl mb-6">📚</div>
            <h4 className="text-3xl font-bold mb-4">No students yet</h4>
            <p className="text-xl text-gray-600 mb-8">Add your first student to get started</p>
            <Link
              href="/children/add"
              className="inline-block px-10 py-5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-xl"
            >
              Add Your First Student
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-6">
            {children.map((child) => (
              <div key={child.id} className="bg-white rounded-2xl border-2 p-8">
                <div className="mb-6">
                  <h4 className="text-2xl font-bold mb-1">{child.first_name}</h4>
                  <div className="text-sm text-gray-500">{child.grade_level}</div>
                </div>
                <Link
                  href={`/learn/${child.id}`}
                  className="block w-full text-center px-6 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-lg"
                >
                  Start Session
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
