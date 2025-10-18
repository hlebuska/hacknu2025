"use client";

import { Box, ScrollArea } from "@mantine/core";
import { ChatMessage, type Message } from "./chat-message";
import { ChatInput } from "./chat-input";
import { ChatHeader } from "./chat-header";
import { useState, useEffect, useRef } from "react";
import { apiConfig } from "../../../config/api";

export function Chatbot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: "Hello! How can I help you today?",
      role: "assistant",
      timestamp: new Date(),
    },
  ]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(apiConfig.endpoints.chatWs);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      const responseText = event.data;
      if (responseText !== "connected") {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            content: responseText.replace("echo: ", ""),
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
  }, []);

  const handleSendMessage = (message: string) => {
    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      role: "user",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Send message via WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
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
