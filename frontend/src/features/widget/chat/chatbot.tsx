"use client";

import { Box, ScrollArea } from "@mantine/core";
import { ChatMessage, type Message } from "./chat-message";
import { ChatInput } from "./chat-input";
import { ChatHeader } from "./chat-header";
import { useState, useEffect, useRef } from "react";
import { apiConfig } from "../../../config/api";

interface ChatbotProps {
  conversationId?: string;
  applicationId?: string;
  vacancyId?: string;
  sessionId?: string;
}

export function Chatbot({
  conversationId,
  applicationId,
  vacancyId,
  sessionId = "default",
}: ChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content:
        "Hello! I'm your AI recruitment assistant. I can help you understand how your qualifications match job requirements, answer questions about positions, or assist with interview preparation. How can I help you today?",
      role: "assistant",
      timestamp: new Date(),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Initialize WebSocket connon
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [sessionId, conversationId]);

  const connectWebSocket = () => {
    const wsUrl = `${apiConfig.wsUrl}/api/v1/chat/ws/${sessionId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");
      // Send initial setup message
      if (conversationId) {
        ws.send(
          JSON.stringify({
            type: "setup",
            conversation_id: conversationId,
            application_id: applicationId,
            vacancy_id: vacancyId,
          })
        );
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "connection") {
          console.log("Successfully connected:", data);
        } else if (data.type === "message") {
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now().toString(),
              content: data.content,
              role: "assistant",
              timestamp: new Date(),
            },
          ]);
          setLoading(false);
        } else if (data.type === "error") {
          console.error("Chat error:", data.message);
          setLoading(false);
        }
      } catch (e) {
        console.error("Error parsing WebSocket message:", e);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setLoading(false);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
    };
  };

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;

    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      role: "user",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        // Send via WebSocket
        wsRef.current.send(
          JSON.stringify({
            message,
            conversation_id: conversationId,
            application_id: applicationId,
            vacancy_id: vacancyId,
          })
        );
      } else {
        // Send via HTTP
        const params = new URLSearchParams({
          message,
          ...(conversationId && { conversation_id: conversationId }),
          ...(applicationId && { application_id: applicationId }),
          ...(vacancyId && { vacancy_id: vacancyId }),
        });

        const response = await fetch(
          `${apiConfig.baseUrl}${apiConfig.endpoints.chat}?${params}`,
          {
            method: "POST",
          }
        );

        if (!response.ok) {
          throw new Error(`Chat error: ${response.statusText}`);
        }

        const data = await response.json();

        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            content: data.response,
            role: "assistant",
            timestamp: new Date(),
          },
        ]);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          content:
            "Sorry, I encountered an error processing your message. Please try again.",
          role: "assistant",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        border: "1px solid #e9ecef",
        borderRadius: "12px",
        overflow: "hidden",
        backgroundColor: "white",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
      }}
    >
      <ChatHeader />

      <ScrollArea
        style={{
          flex: 1,
          backgroundColor: "#f8f9fa",
        }}
        viewportRef={scrollRef}
      >
        <Box style={{ padding: "16px" }}>
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {loading && (
            <Box style={{ padding: "12px", textAlign: "center" }}>
              <div
                style={{
                  display: "inline-block",
                  padding: "8px 12px",
                  backgroundColor: "#f1f3f5",
                  borderRadius: "12px",
                  color: "#666",
                  fontSize: "14px",
                }}
              >
                AI is thinking...
              </div>
            </Box>
          )}
        </Box>
      </ScrollArea>

      <ChatInput onSend={handleSendMessage} disabled={loading} />
    </Box>
  );
}
