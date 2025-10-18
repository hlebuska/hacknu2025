"use client";

import { Box, ScrollArea } from "@mantine/core";
import { ChatMessage, type Message } from "./chat-message";
import { ChatInput } from "./chat-input";
import { ChatHeader } from "./chat-header";
import { useState, useEffect, useRef } from "react";
import { apiConfig } from "../../../config/api";

interface ChatbotProps {
  applicationId: string;
}

export function Chatbot({ applicationId }: ChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    // Connect to WebSocket with application ID
    const ws = new WebSocket(apiConfig.endpoints.chatWs(applicationId));
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected for application:", applicationId);
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
  }, [applicationId]);

  const handleSendMessage = (message: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      role: "user",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    const conversationHistory = [...messages, userMessage].map((msg) => ({
      role: msg.role,
      content: msg.content,
    }));

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const payload = {
        message: message,
        history: conversationHistory,
      };
      wsRef.current.send(JSON.stringify(payload));
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
