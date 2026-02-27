'use client';

import { useState, useRef, useEffect } from 'react';
import { api, QueryResponse } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  tools?: string[];
  reasoning?: string | null;
}

interface ChatSession {
  session_id: string;
  last_message: string;
  message_count: number;
  created_at: string;
}

export default function QueryChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID());
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [showSidebar, setShowSidebar] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load chat sessions on mount
  useEffect(() => {
    api.listChats().then(setSessions).catch(() => {});
  }, []);

  const loadSession = async (sid: string) => {
    try {
      const msgs = await api.getChat(sid);
      setMessages(msgs.map(m => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
        tools: m.tools_used,
        reasoning: m.reasoning,
      })));
      setSessionId(sid);
      setShowSidebar(false);
    } catch {
      // ignore
    }
  };

  const newChat = () => {
    setSessionId(crypto.randomUUID());
    setMessages([]);
    setShowSidebar(false);
  };

  const send = async () => {
    const msg = input.trim();
    if (!msg || loading) return;

    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setLoading(true);

    try {
      const res: QueryResponse = await api.query(msg, sessionId);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.response,
          tools: res.tools_used,
          reasoning: res.reasoning,
        },
      ]);
      // Refresh sessions list
      api.listChats().then(setSessions).catch(() => {});
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
    <div className="flex h-[calc(100vh-12rem)]">
      {/* Chat History Sidebar */}
      <div className={`${showSidebar ? 'w-64' : 'w-0'} transition-all overflow-hidden border-r border-[var(--border)]`}>
        <div className="w-64 h-full flex flex-col">
          <div className="p-3 border-b border-[var(--border)]">
            <button onClick={newChat}
              className="w-full py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-xs font-medium transition">
              + New Chat
            </button>
          </div>
          <div className="flex-1 overflow-y-auto">
            {sessions.map(s => (
              <button key={s.session_id} onClick={() => loadSession(s.session_id)}
                className={`w-full text-left px-3 py-2.5 text-xs border-b border-[var(--border)] hover:bg-[var(--bg-primary)] transition ${
                  s.session_id === sessionId ? 'bg-brand-500/10 border-l-2 border-l-brand-500' : ''
                }`}>
                <div className="text-[var(--text-primary)] truncate">{s.last_message}</div>
                <div className="text-[var(--text-secondary)] mt-0.5">{s.message_count} messages</div>
              </button>
            ))}
            {sessions.length === 0 && (
              <div className="p-3 text-xs text-[var(--text-secondary)]">No chat history yet</div>
            )}
          </div>
        </div>
      </div>

      {/* Main Chat */}
      <div className="flex-1 flex flex-col max-w-3xl">
        {/* Toggle sidebar */}
        <div className="flex items-center gap-2 mb-3">
          <button onClick={() => setShowSidebar(!showSidebar)}
            className="text-xs px-3 py-1.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition">
            {showSidebar ? '← Hide History' : '☰ Chat History'}
          </button>
          <span className="text-xs text-[var(--text-secondary)]">
            Session: {sessionId.slice(0, 8)}...
          </span>
        </div>

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
                    'What Airbyte connectors are available for Stripe?',
                    'What is our remote work policy?',
                    'Show salary benchmarks for Engineers in SF',
                    'Run compliance check for California hires',
                  ].map((q) => (
                    <button key={q} onClick={() => setInput(q)}
                      className="text-xs px-3 py-1.5 rounded-full bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-brand-500/50 transition">
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-xl px-4 py-3 text-sm ${
                m.role === 'user'
                  ? 'bg-brand-600 text-white'
                  : 'bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text-primary)]'
              }`}>
                <div className="whitespace-pre-wrap">{m.content}</div>
                {m.tools && m.tools.length > 0 && (
                  <div className="mt-2 flex gap-1.5 flex-wrap">
                    {m.tools.map((t) => (
                      <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300">
                        🔧 {t}
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
          <button onClick={send} disabled={loading || !input.trim()}
            className="px-5 py-3 rounded-lg bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed">
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
