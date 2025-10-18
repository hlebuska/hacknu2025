"use client";

import { Box, ScrollArea } from "@mantine/core";
import { ChatMessage, type Message } from "./chat-message";
import { ChatInput } from "./chat-input";
import { ChatHeader } from "./chat-header";
import { useState, useEffect, useRef } from "react";
import { apiConfig } from "../../../config/api";

interface ChatbotProps {
  applicationContext?: {
    id: string;
    vacancy_id: string;
    first_name: string;
    last_name: string;
    email: string;
    resume_pdf: string;
    matching_score: number;
    matching_sections: {
      requirements: Array<{
        vacancy_req: string;
        user_req_data: string;
        match_percent: number;
      }>;
      FIT_SCORE: number;
    };
  };
}

export function Chatbot({ applicationContext }: ChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: applicationContext
        ? `Hello ${applicationContext.first_name}! I'm here to help clarify your application. I can see your matching score is ${applicationContext.matching_score}%. Let me ask you a few questions to better understand your qualifications.`
        : "Hello! How can I help you today?",
      role: "assistant",
      timestamp: new Date(),
    },
  ]);
  const wsRef = useRef<WebSocket | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(apiConfig.endpoints.chatWs);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");

      // Send initial context if available
      if (applicationContext && ws.readyState === WebSocket.OPEN) {
        const initialPayload = {
          message: "Initialize conversation with application context",
          history: [],
          context: applicationContext,
        };
        ws.send(JSON.stringify(initialPayload));
      }
    };

    ws.onmessage = (event) => {
      const responseText = event.data;
      if (responseText !== "connected") {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            content: responseText,
            role: "assistant",
            timestamp: new Date(),
          },
        ]);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
    };

    return () => {
      ws.close();
    };
  }, [applicationContext]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, [messages]);

  const handleSendMessage = (message: string) => {
    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      role: "user",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Prepare message history (excluding the initial greeting)
    const conversationHistory = [...messages, userMessage]
      .filter((msg) => msg.id !== "1") // Exclude initial greeting
      .map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

    // Send message with history and context via WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const payload = {
        message: message,
        history: conversationHistory,
        context: applicationContext,
      };
      wsRef.current.send(JSON.stringify(payload));
    } else {
      console.error("WebSocket is not connected");
    }
  };

  return (
    <Box
      style={{
        width: "100vw",
        height: "100vh",
        margin: "0 auto",
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
        ref={scrollAreaRef}
        style={{
          flex: 1,
          backgroundColor: "#f8f9fa",
        }}
      >
        <Box style={{ padding: "8px 0" }}>
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
        </Box>
      </ScrollArea>

      <ChatInput onSend={handleSendMessage} />
    </Box>
  );
}
