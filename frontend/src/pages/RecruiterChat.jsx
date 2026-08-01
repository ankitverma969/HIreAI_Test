import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ChatService } from '../services/chatService';
import { useNotifications } from '../context/NotificationContext';
import { Button, EmptyState } from '../components';
import styles from './RecruiterChat.module.css';

const SESSION_ID = 'default';

const SUGGESTED_QUESTIONS = [
  'Who ranked first?',
  'Who has the strongest Python skills?',
  'Which candidates know AWS?',
  'Who has Machine Learning experience?',
  'Which candidate has the highest confidence score?',
  'Who should be interviewed first?',
  'Which skills are commonly missing?',
  'Show candidates with Docker experience.',
  'Which resumes mention LangGraph?',
];

const renderInline = (text) => {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    return <React.Fragment key={index}>{part}</React.Fragment>;
  });
};

const MarkdownMessage = ({ content }) => {
  const blocks = String(content || '').split(/```/g);

  return (
    <div className={styles.markdown}>
      {blocks.map((block, blockIndex) => {
        if (blockIndex % 2 === 1) {
          return (
            <pre key={blockIndex} className={styles.codeBlock}>
              <code>{block}</code>
            </pre>
          );
        }

        return block.split('\n').map((line, lineIndex) => {
          if (!line.trim()) {
            return <div key={`${blockIndex}-${lineIndex}`} className={styles.lineBreak} />;
          }
          if (line.trim().startsWith('- ')) {
            return (
              <div key={`${blockIndex}-${lineIndex}`} className={styles.bulletLine}>
                <span />
                <p>{renderInline(line.trim().slice(2))}</p>
              </div>
            );
          }
          return <p key={`${blockIndex}-${lineIndex}`}>{renderInline(line)}</p>;
        });
      })}
    </div>
  );
};

export const RecruiterChat = () => {
  const { showError, showSuccess } = useNotifications();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await ChatService.getHistory(SESSION_ID);
        setMessages(response.data.messages || []);
      } catch (e) {
        showError(e.message || 'Failed to load chat history.');
      }
    };
    loadHistory();
  }, [showError]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const hasMessages = messages.length > 0;

  const canSubmit = useMemo(() => input.trim().length > 0 && !isLoading, [input, isLoading]);

  const askQuestion = async (question) => {
    const cleanQuestion = question.trim();
    if (!cleanQuestion || isLoading) return;

    const optimisticUserMessage = {
      role: 'user',
      content: cleanQuestion,
      timestamp: new Date().toISOString(),
      metadata: {},
    };

    setMessages((prev) => [...prev, optimisticUserMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await ChatService.ask(cleanQuestion, SESSION_ID);
      setMessages(response.data.history || []);
    } catch (e) {
      showError(e.message || 'Failed to ask recruiter assistant.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (canSubmit) askQuestion(input);
  };

  const clearHistory = async () => {
    try {
      const response = await ChatService.clearHistory(SESSION_ID);
      setMessages(response.data.messages || []);
      showSuccess('Chat history cleared.');
    } catch (e) {
      showError(e.message || 'Failed to clear chat history.');
    }
  };

  return (
    <div className={styles.page}>
      <section className={styles.chatShell}>
        <div className={styles.chatHeader}>
          <div>
            <h2>AI Recruiter Chat</h2>
            <p>Answers use only uploaded resumes, the job description, rankings, and reports.</p>
          </div>
          <Button variant="secondary" onClick={clearHistory} disabled={!hasMessages || isLoading}>
            Clear History
          </Button>
        </div>

        <div className={styles.messages}>
          {!hasMessages && !isLoading && (
            <EmptyState
              title="Ask About The Current Screening Run"
              description="Use the suggested questions below or ask a follow-up after the assistant answers."
            />
          )}

          {messages.map((message, index) => (
            <div
              key={`${message.role}-${message.timestamp}-${index}`}
              className={`${styles.messageRow} ${message.role === 'user' ? styles.userRow : styles.assistantRow}`}
            >
              <div className={styles.avatar}>{message.role === 'user' ? 'HR' : 'AI'}</div>
              <div className={styles.bubble}>
                {message.role === 'assistant' ? (
                  <MarkdownMessage content={message.content} />
                ) : (
                  <p>{message.content}</p>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className={`${styles.messageRow} ${styles.assistantRow}`}>
              <div className={styles.avatar}>AI</div>
              <div className={`${styles.bubble} ${styles.typing}`}>
                <span />
                <span />
                <span />
              </div>
            </div>
          )}
          <div ref={scrollRef} />
        </div>

        <div className={styles.suggestions}>
          {SUGGESTED_QUESTIONS.map((question) => (
            <button
              key={question}
              type="button"
              onClick={() => askQuestion(question)}
              disabled={isLoading}
            >
              {question}
            </button>
          ))}
        </div>

        <form className={styles.inputBar} onSubmit={handleSubmit}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about rankings, skills, gaps, projects, or interview priority..."
            rows={2}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                if (canSubmit) askQuestion(input);
              }
            }}
          />
          <Button type="submit" disabled={!canSubmit} loading={isLoading}>
            Send
          </Button>
        </form>
      </section>
    </div>
  );
};

export default RecruiterChat;
