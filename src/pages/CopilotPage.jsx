import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BotMessageSquare,
  Send,
  Sparkles,
  ShieldAlert,
  ArrowRight,
  TrendingDown,
  DollarSign,
  Layers,
  HelpCircle,
  CheckCircle2,
  Terminal,
  User,
  Zap
} from 'lucide-react';
import MetricCard from '../components/common/MetricCard';
import Badge from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useTelemetry } from '../context/TelemetryContext';
import { copilotApi } from '../api/copilotApi';

export default function CopilotPage() {
  const navigate = useNavigate();
  const { formatCurrency, refreshKey } = useTelemetry();
  const [messages, setMessages] = useState([
    {
      id: 'init-1',
      sender: 'assistant',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      content: {
        title: "CYBERVAL Executive Cyber-Risk Intelligence AI",
        summary: "I am connected to the **CYBERVAL FAIR engine**, real-time attack graph telemetry, and regulatory baselines (RBI / SEBI CSCRF). How can I assist your cyber risk analysis or board preparation today?",
        metrics: [
          { label: "Enterprise Risk Score", value: "71 / 100", badge: "High Risk" },
          { label: "Expected Annual Loss", value: "₹18.4 Cr", badge: "EAL" },
          { label: "Potential Risk Reduction", value: "₹6.5 Cr", badge: "ROSI 400%" }
        ],
        recommendedAction: "Click one of the suggested executive questions below or type your custom query.",
        deepLinks: [
          { label: "Review Executive KPIs", path: "/executive" },
          { label: "Simulate Controls in What-If", path: "/simulation" }
        ]
      }
    }
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
        console.error('Failed to load copilot prompts:', err);
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
      text: text
    };

    setMessages(prev => [...prev, userMessage]);
    setInputQuery('');
    setIsTyping(true);

    try {
      const response = await copilotApi.askCopilot(text);
      
      setTimeout(() => {
        const aiMessage = {
          id: `ai-${Date.now()}`,
          sender: 'assistant',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          content: response
        };
        setMessages(prev => [...prev, aiMessage]);
        setIsTyping(false);
      }, 400);
    } catch (err) {
      console.error('Copilot query error:', err);
      setIsTyping(false);
      setMessages(prev => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          content: {
            title: "Analysis Error",
            summary: "Encountered an issue communicating with the cyber intelligence model.",
            metrics: [],
            deepLinks: []
          }
        }
      ]);
    }
  };

  return (
    <div className="space-y-4 max-w-5xl mx-auto h-[calc(100vh-7.5rem)] flex flex-col justify-between">
      
      {/* Copilot Header */}
      <div className="flex items-center justify-between p-4 rounded-lg cyber-card border-cv-border flex-shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cv-blueLight border border-blue-200 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-cv-blue" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-cv-text font-sans">CYBERVAL AI Copilot</h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cv-blueLight text-cv-blue border border-blue-200">
                FAIR & CYBER-RISK INTEL
              </span>
            </div>
            <p className="text-xs text-cv-muted font-mono">
              Ask natural language risk questions backed by real-time attack graph & financial exposure models.
            </p>
          </div>
        </div>

        <div className="hidden sm:flex items-center space-x-2 font-mono text-xs text-cv-muted">
          <span className="w-2 h-2 rounded-full bg-cv-success" />
          <span>MODEL ONLINE</span>
        </div>
      </div>

      {/* Chat Messages Log Area */}
      <div className="flex-1 overflow-y-auto space-y-4 p-2 font-mono text-xs pr-2">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.sender === 'user' ? (
              <div className="max-w-xl p-3.5 rounded-2xl bg-cv-blue text-white shadow-card-md">
                <div className="flex items-center justify-between space-x-4 mb-1 text-[10px] text-blue-200">
                  <span className="font-bold flex items-center"><User className="w-3 h-3 mr-1" /> Executive Prompt</span>
                  <span>{msg.timestamp}</span>
                </div>
                <p className="text-sm font-sans font-medium">{msg.text}</p>
              </div>
            ) : (
              <div className="max-w-2xl p-4 rounded-2xl bg-white border border-cv-border shadow-card space-y-3">
                
                {/* Assistant Header */}
                <div className="flex items-center justify-between border-b border-cv-border pb-2 text-[10px] text-cv-muted">
                  <span className="flex items-center space-x-1.5 text-cv-blue font-bold">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>CYBERVAL INTELLIGENCE</span>
                  </span>
                  <span>{msg.timestamp}</span>
                </div>

                {/* Title & Summary */}
                <div>
                  <h3 className="text-sm font-bold text-cv-text font-sans">{msg.content.title}</h3>
                  <div
                    className="text-xs text-cv-muted mt-1 leading-relaxed space-y-1"
                    dangerouslySetInnerHTML={{
                      __html: msg.content.summary?.replace(/\*\*(.*?)\*\*/g, '<strong class="text-cv-text font-bold">$1</strong>')
                    }}
                  />
                </div>

                {/* Telemetry Metric Cards in AI Response */}
                {msg.content.metrics && msg.content.metrics.length > 0 && (
                  <div className="grid grid-cols-2 sm:grid-cols-2 gap-2 pt-1">
                    {msg.content.metrics.map((m, idx) => (
                      <div key={idx} className="p-2.5 rounded-lg bg-cv-bg border border-cv-border">
                        <div className="flex justify-between text-[10px] text-cv-muted">
                          <span>{m.label}</span>
                          {m.badge && <span className="text-cv-blue font-bold">{m.badge}</span>}
                        </div>
                        <div className="text-sm font-bold text-cv-text font-sans mt-0.5">{m.value}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Recommended Next Step */}
                {msg.content.recommendedAction && (
                  <div className="p-2.5 rounded-lg bg-cv-blueLight border border-blue-200 text-[11px] text-cv-blue">
                    <strong>Recommended Action:</strong> {msg.content.recommendedAction}
                  </div>
                )}

                {/* Deep Link Triggers */}
                {msg.content.deepLinks && msg.content.deepLinks.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-2 border-t border-cv-border">
                    {msg.content.deepLinks.map((link, idx) => (
                      <button
                        key={idx}
                        onClick={() => navigate(link.path)}
                        className="px-2.5 py-1 rounded bg-cv-bg border border-cv-border hover:bg-cv-blue hover:text-white hover:border-cv-blue text-cv-muted font-bold transition-all text-[10px] flex items-center space-x-1"
                      >
                        <span>{link.label}</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    ))}
                  </div>
                )}

              </div>
            )}
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="p-3 rounded-2xl bg-white border border-cv-border text-cv-muted flex items-center space-x-2 shadow-card">
              <Sparkles className="w-4 h-4 text-cv-blue animate-spin" />
              <span className="text-xs font-mono">Analyzing cyber telemetry & calculating risk deltas...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Executive Prompts Bar */}
      <div className="space-y-2 flex-shrink-0 pt-2">
        <div className="flex items-center space-x-2 text-[10px] font-mono text-cv-muted">
          <Zap className="w-3 h-3 text-cv-warning" />
          <span>Executive Quick Prompts:</span>
        </div>
        <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
          {suggestedPrompts.slice(0, 4).map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(p)}
              className="px-3 py-1 rounded-lg bg-white hover:bg-cv-blueLight border border-cv-border hover:border-cv-blue text-cv-muted hover:text-cv-blue transition-all truncate max-w-xs"
            >
              "{p}"
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2 bg-white p-2 rounded-xl border border-cv-border focus-within:border-cv-blue shadow-card transition-all"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask anything (e.g. 'What should we fix first?' or 'What happens if we implement MFA?')..."
            className="flex-1 bg-transparent px-3 py-2 text-xs font-mono text-cv-text focus:outline-none placeholder-cv-muted"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isTyping}
            className="p-2.5 rounded-lg bg-cv-blue hover:bg-blue-700 disabled:opacity-50 text-white transition-all shadow-sm"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

    </div>
  );
}
