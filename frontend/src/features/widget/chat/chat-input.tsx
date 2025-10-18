"use client";

import type React from "react";

import { ActionIcon, Box, Textarea } from "@mantine/core";
import { SendHorizontal } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !disabled) {
      e.preventDefault();
      const target = e.target as HTMLTextAreaElement;
      if (target.value.trim()) {
        onSend(target.value);
        target.value = "";
      }
    }
  };

  const handleSendClick = () => {
    if (disabled) return;
    const textarea = document.querySelector("textarea");
    if (textarea && textarea.value.trim()) {
      onSend(textarea.value);
      textarea.value = "";
    }
  };

  return (
    <Box
      style={{
        padding: "16px",
        borderTop: "1px solid #e9ecef",
        backgroundColor: "white",
      }}
    >
      <Box style={{ display: "flex", gap: "8px", alignItems: "flex-end" }}>
        <Textarea
          placeholder="Type your message..."
          autosize
          minRows={1}
          maxRows={4}
          onKeyDown={handleKeyPress}
          style={{ flex: 1 }}
          styles={{
            input: {
              borderRadius: "20px",
              padding: "12px 16px",
            },
          }}
        />
        <ActionIcon
          size="lg"
          radius="xl"
          color="blue"
          variant="filled"
          onClick={handleSendClick}
          disabled={disabled}
          style={{ marginBottom: "2px" }}
        >
          <SendHorizontal />
        </ActionIcon>
      </Box>
    </Box>
  );
}
