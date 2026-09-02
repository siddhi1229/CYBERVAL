import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BotMessageSquare,
  Send,
  Sparkles,
  ShieldAlert,
  HelpCircle,
  CheckCircle2,
  Terminal,
  User,
  Zap
} from 'lucide-react';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTelemetry } from '../context/TelemetryContext';
import { copilotApi } from '../api/copilotApi';
import { NO_DATA } from '../utils/formatters';

export default function CopilotPage() {
  const navigate = useNavigate();
  const { refreshKey } = useTelemetry();

  const [messages, setMessages] = useState([
    {
      id: 'init-1',
      sender: 'assistant',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      text: "I am connected to the CYBERVAL live risk decision support engine (`/api/ai/query`). Ask any question regarding enterprise expected loss, attack paths, or regulatory compliance.",
    },
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [suggestedPrompts, setSuggestedPrompts] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    async function loadPrompts() {
      try {
        const prompts = await copilotApi.getSuggestedPrompts();
        setSuggestedPrompts(prompts);
      } catch (err) {
        console.error('Failed to load prompts:', err);
      }
    }
    loadPrompts();
  }, [refreshKey]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = async (queryText) => {
    const text = queryText || inputQuery;
    if (!text.trim()) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      text: text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    setIsTyping(true);

    try {
      const response = await copilotApi.askCopilot(text);
      const aiAnswer = response?.answer || NO_DATA;

      const aiMessage = {
        id: `ai-${Date.now()}`,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        text: aiAnswer,
        sourceRiskIds: response?.source_risk_ids || [],
        generatedAt: response?.generated_at,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error('Copilot query error:', err);
      const errorMessage = {
        id: `err-${Date.now()}`,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        text: `Backend Error: ${err.response?.data?.detail || err.message || NO_DATA}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="space-y-4 max-w-5xl mx-auto h-[calc(100vh-7rem)] flex flex-col justify-between">
      
      {/* Header */}
      <div className="p-4 rounded-lg cyber-card border-cv-border flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-cv-blue text-white">
            <BotMessageSquare className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-extrabold text-cv-text font-sans">
              CYBERVAL Risk-Grounded AI Copilot
            </h1>
            <p className="text-xs text-cv-muted font-mono">
              Live Decision Support API (`POST /api/ai/query`)
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-cv-success animate-pulse" />
          <span className="text-xs font-mono text-cv-success font-bold">ONLINE</span>
        </div>
      </div>

      {/* Messages Thread Container */}
      <div className="flex-1 overflow-y-auto cyber-card rounded-lg border-cv-border p-5 space-y-4">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  isUser ? 'bg-slate-700 text-white' : 'bg-cv-blue text-white'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-2xl p-4 rounded-xl font-mono text-xs ${
                  isUser
                    ? 'bg-cv-blue text-white rounded-tr-none'
                    : 'bg-cv-bg text-cv-text border border-cv-border rounded-tl-none space-y-2'
                }`}
              >
                <div className="flex items-center justify-between text-[10px] opacity-75 mb-1">
                  <span>{isUser ? 'You' : 'CYBERVAL Copilot'}</span>
                  <span>{msg.timestamp}</span>
                </div>

                <p className="font-sans text-xs leading-relaxed whitespace-pre-wrap">{msg.text}</p>

                {msg.sourceRiskIds && msg.sourceRiskIds.length > 0 && (
                  <div className="pt-2 border-t border-cv-border/50 text-[10px] text-cv-muted">
                    Source Risk References: {msg.sourceRiskIds.map(id => `#${id}`).join(', ')}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="flex items-center space-x-2 text-cv-muted font-mono text-xs pl-11">
            <span className="w-2 h-2 rounded-full bg-cv-blue animate-bounce" />
            <span className="w-2 h-2 rounded-full bg-cv-blue animate-bounce [animation-delay:0.2s]" />
            <span className="w-2 h-2 rounded-full bg-cv-blue animate-bounce [animation-delay:0.4s]" />
            <span>Evaluating risk intelligence...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts Pill Bar */}
      <div className="flex flex-wrap gap-2 pt-1 font-mono text-[11px]">
        {suggestedPrompts.map((prompt, i) => (
          <button
            key={i}
            onClick={() => handleSend(prompt)}
            className="px-3 py-1 rounded-full bg-white border border-cv-border hover:border-cv-blue text-cv-muted hover:text-cv-blue transition-all"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Query Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center space-x-2"
      >
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder="Ask a question about enterprise risk, crown jewels, or attack paths..."
          className="flex-1 p-3 rounded-lg cyber-card border border-cv-border focus:border-cv-blue focus:outline-none font-mono text-xs text-cv-text"
        />
        <button
          type="submit"
          disabled={!inputQuery.trim() || isTyping}
          className="p-3 rounded-lg bg-cv-blue hover:bg-blue-700 text-white font-bold transition-all disabled:opacity-50"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>

    </div>
  );
}
