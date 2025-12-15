'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function LearningSessionPage() {
  const params = useParams();
  const childId = params.childId as string;

  const [child, setChild] = useState<any>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadChild();
  }, []);

  const loadChild = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      window.location.href = '/login';
      return;
    }

    try {
      const response = await fetch('https://web-production-5e612.up.railway.app/api/v1/children/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const children = await response.json();
        const currentChild = children.find((c: any) => c.id === parseInt(childId));
        setChild(currentChild);
      }
    } catch (error) {
      console.error('Failed to load child:', error);
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: 'user',
      content: input
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('https://web-production-5e612.up.railway.app/api/v1/conversation/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          child_id: parseInt(childId),
          text: input,
          conversation_id: null
        })
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage: Message = {
          role: 'assistant',
          content: data.text
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('Failed to get response');
      }
    } catch (error) {
      const errorMessage: Message = {
        role: 'assistant',
        content: 'I had trouble understanding that. Could you try asking in a different way?'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col bg-neutral-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="text-neutral-600 hover:text-neutral-900 font-medium"
            >
              ← Dashboard
            </Link>
            <div className="h-6 w-px bg-neutral-300"></div>
            <div>
              <h1 className="font-bold text-lg text-neutral-900">
                {child?.first_name}'s Learning Session
              </h1>
              <p className="text-sm text-neutral-600">{child?.grade_level}</p>
            </div>
          </div>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-8">
          {messages.length === 0 ? (
            <div className="text-center py-16">
              <div className="inline-block bg-white rounded-2xl border border-neutral-200 p-12 shadow-sm">
                <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-neutral-900 mb-2">
                  Hi {child?.first_name}!
                </h2>
                <p className="text-neutral-600 max-w-md">
                  I'm Nia, your learning assistant. Ask me anything you'd like to learn about!
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-2xl px-6 py-4 rounded-2xl ${
                      msg.role === 'user'
                        ? 'bg-primary-500 text-white'
                        : 'bg-white border border-neutral-200 text-neutral-900'
                    }`}
                  >
                    <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-neutral-200 px-6 py-4 rounded-2xl">
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce delay-100"></div>
                        <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce delay-200"></div>
                      </div>
                      <span className="text-neutral-600">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t bg-white">
        <form onSubmit={sendMessage} className="max-w-4xl mx-auto px-6 py-6">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              className="flex-1 px-6 py-4 border border-neutral-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition text-lg"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-primary-500 hover:bg-primary-600 text-white px-8 py-4 rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
