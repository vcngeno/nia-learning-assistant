'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function AddStudentPage() {
  const [firstName, setFirstName] = useState('');
  const [nickname, setNickname] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [gradeLevel, setGradeLevel] = useState('');
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        window.location.href = '/login';
        return;
      }

      const response = await fetch('https://web-production-5e612.up.railway.app/api/v1/children/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          first_name: firstName,
          nickname: nickname || null,
          date_of_birth: dateOfBirth,
          grade_level: gradeLevel,
          pin: pin,
          preferred_language: 'en'
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to add student');
      }

      window.location.href = '/dashboard';
    } catch (err: any) {
      setError(err.message || 'Failed to add student. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="border-b">
        <div className="max-w-4xl mx-auto px-6 py-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Nia - Add Student</h1>
          <Link href="/dashboard" className="px-6 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg font-semibold">
            Back to Dashboard
          </Link>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h2 className="text-4xl font-bold mb-2">Add a Student</h2>
          <p className="text-xl text-gray-600">Create a profile for your child to start learning</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl border-2 p-8 space-y-6">
          {error && (
            <div className="bg-red-50 border-2 border-red-200 text-red-700 px-6 py-4 rounded-xl font-semibold">
              {error}
            </div>
          )}

          <div>
            <label className="block text-lg font-bold mb-2">First Name *</label>
            <input
              type="text"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              className="w-full px-4 py-3 border-2 rounded-xl text-lg"
              placeholder="Emma"
              required
            />
          </div>

          <div>
            <label className="block text-lg font-bold mb-2">Nickname (Optional)</label>
            <input
              type="text"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              className="w-full px-4 py-3 border-2 rounded-xl text-lg"
              placeholder="Em"
            />
          </div>

          <div>
            <label className="block text-lg font-bold mb-2">Date of Birth *</label>
            <input
              type="date"
              value={dateOfBirth}
              onChange={(e) => setDateOfBirth(e.target.value)}
              className="w-full px-4 py-3 border-2 rounded-xl text-lg"
              required
            />
          </div>

          <div>
            <label className="block text-lg font-bold mb-2">Grade Level *</label>
            <select
              value={gradeLevel}
              onChange={(e) => setGradeLevel(e.target.value)}
              className="w-full px-4 py-3 border-2 rounded-xl text-lg"
              required
            >
              <option value="">Select grade level...</option>
              <option value="Kindergarten">Kindergarten</option>
              <option value="1st Grade">1st Grade</option>
              <option value="2nd Grade">2nd Grade</option>
              <option value="3rd Grade">3rd Grade</option>
              <option value="4th Grade">4th Grade</option>
              <option value="5th Grade">5th Grade</option>
              <option value="6th Grade">6th Grade</option>
              <option value="7th Grade">7th Grade</option>
              <option value="8th Grade">8th Grade</option>
              <option value="9th Grade">9th Grade</option>
              <option value="10th Grade">10th Grade</option>
              <option value="11th Grade">11th Grade</option>
              <option value="12th Grade">12th Grade</option>
            </select>
          </div>

          <div>
            <label className="block text-lg font-bold mb-2">Student PIN (4 digits) *</label>
            <input
              type="text"
              value={pin}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 4))}
              className="w-full px-4 py-3 border-2 rounded-xl text-lg"
              placeholder="1234"
              maxLength={4}
              pattern="[0-9]{4}"
              required
            />
            <p className="text-sm text-gray-500 mt-2">
              Your child will use this 4-digit PIN to access their learning sessions
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full px-8 py-5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-xl disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Adding Student...' : 'Add Student'}
          </button>
        </form>
      </div>
    </div>
  );
}
