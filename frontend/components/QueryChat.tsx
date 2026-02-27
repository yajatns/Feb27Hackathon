'use client';

import { useState, useRef, useEffect } from 'react';
import { api, QueryResponse } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  tools?: string[];
  reasoning?: string | null;
}

export default function QueryChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async () => {
    const msg = input.trim();
    if (!msg || loading) return;

    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setLoading(true);

    try {
      const res: QueryResponse = await api.query(msg);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.response,
          tools: res.tools_used,
          reasoning: res.reasoning,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${err instanceof Error ? err.message : 'Request failed'}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] max-w-3xl">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-3">
              <div className="text-2xl">▷</div>
              <div className="text-sm text-[var(--text-secondary)]">
                Ask anything about your back office.
              </div>
              <div className="flex flex-wrap gap-2 justify-center mt-4">
                {[
                  'Hire Sarah Chen as Senior Engineer at $150K',
                  'What is our remote work policy?',
                  'Show salary benchmarks for Engineering',
                  'Run compliance check for recent hires',
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); }}
                    className="text-xs px-3 py-1.5 rounded-full bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-brand-500/50 transition"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-xl px-4 py-3 text-sm ${
                m.role === 'user'
                  ? 'bg-brand-600 text-white'
                  : 'bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-primary)]'
              }`}
            >
              <div className="whitespace-pre-wrap">{m.content}</div>
              {m.tools && m.tools.length > 0 && (
                <div className="mt-2 flex gap-1.5 flex-wrap">
                  {m.tools.map((t) => (
                    <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300">
                      {t}
                    </span>
                  ))}
                </div>
              )}
              {m.reasoning && (
                <details className="mt-2">
                  <summary className="text-xs text-[var(--text-secondary)] cursor-pointer hover:text-[var(--text-primary)]">
                    Show reasoning
                  </summary>
                  <div className="mt-1 text-xs text-[var(--text-secondary)] whitespace-pre-wrap">{m.reasoning}</div>
                </details>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-[var(--bg-card)] border border-[var(--border)] rounded-xl px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse-dot" />
                <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse-dot" style={{ animationDelay: '0.2s' }} />
                <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse-dot" style={{ animationDelay: '0.4s' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder="Ask about policies, salaries, compliance..."
          disabled={loading}
          className="flex-1 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg px-4 py-3 text-sm text-[var(--text-primary)] focus:outline-none focus:border-brand-500 transition disabled:opacity-50"
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          className="px-5 py-3 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </div>
  );
}
