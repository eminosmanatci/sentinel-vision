import { useState } from "react";

import { Send, User, Bot, Loader } from "lucide-react";

import { sendChatQuery } from "../api/client";
import { useChatStore } from "../stores/chatStore";

export function Chat() {
  const [query, setQuery] = useState("");
  const { messages, addMessage, isLoading, setLoading } = useChatStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    const userMessage = query.trim();
    addMessage({ role: "user", content: userMessage });
    setQuery("");
    setLoading(true);

    try {
      const response = await sendChatQuery(userMessage);
      addMessage({
        role: "assistant",
        content: response.answer,
        sources: response.sources,
      });
    } catch (error) {
      addMessage({
        role: "assistant",
        content: "Sorry, I couldn't process your query. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="p-6 border-b border-sentinel-700">
        <h2 className="text-2xl font-bold text-white">AI Security Assistant</h2>
        <p className="text-sentinel-400 mt-1">Ask questions about your security footage</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center py-12 text-sentinel-500">
            <Bot size={48} className="mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">How can I help you?</p>
            <p className="text-sm mt-2">Try: "How many people were detected last night?"</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex gap-4 ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {message.role === "assistant" && (
              <div className="w-8 h-8 rounded-full bg-accent-600 flex items-center justify-center shrink-0">
                <Bot size={16} className="text-white" />
              </div>
            )}

            <div
              className={`max-w-2xl rounded-xl p-4 ${
                message.role === "user"
                  ? "bg-accent-600 text-white"
                  : "bg-sentinel-800 border border-sentinel-700"
              }`}
            >
              <p className="text-sm leading-relaxed">{message.content}</p>

              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-sentinel-700">
                  <p className="text-xs text-sentinel-400 mb-2">Sources:</p>
                  <div className="space-y-1">
                    {message.sources.map((source, i) => (
                      <div
                        key={i}
                        className="text-xs text-sentinel-300 bg-sentinel-700/50 rounded px-2 py-1"
                      >
                        {source.timestamp.toFixed(1)}s: {source.description}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {message.role === "user" && (
              <div className="w-8 h-8 rounded-full bg-sentinel-600 flex items-center justify-center shrink-0">
                <User size={16} className="text-white" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-4">
            <div className="w-8 h-8 rounded-full bg-accent-600 flex items-center justify-center shrink-0">
              <Loader size={16} className="text-white animate-spin" />
            </div>
            <div className="bg-sentinel-800 border border-sentinel-700 rounded-xl p-4">
              <p className="text-sm text-sentinel-300">Analyzing records...</p>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-6 border-t border-sentinel-700">
        <form onSubmit={handleSubmit} className="flex gap-4">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about your security footage..."
            className="flex-1 bg-sentinel-800 border border-sentinel-600 rounded-xl px-4 py-3 text-sm text-white placeholder-sentinel-500 focus:outline-none focus:border-accent-500 transition-colors"
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-6 py-3 bg-accent-600 hover:bg-accent-500 disabled:bg-sentinel-700 disabled:text-sentinel-500 text-white rounded-xl font-medium transition-colors flex items-center gap-2"
          >
            <Send size={16} />
            Send
          </button>
        </form>
      </div>
    </div>
  );
}