import { Avatar, Box, Text } from "@mantine/core";

export interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
}

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <Box
      style={{
        display: "flex",
        gap: "12px",
        padding: "12px",
        flexDirection: isUser ? "row-reverse" : "row",
      }}
    >
      <Avatar
        size="sm"
        radius="xl"
        color={isUser ? "blue" : "gray"}
        style={{ flexShrink: 0 }}
      >
        {isUser ? "U" : "AI"}
      </Avatar>

      <Box style={{ flex: 1, maxWidth: "70%" }}>
        <Text
          size="sm"
          style={{
            padding: "8px 4px",
            borderRadius: "12px",
            backgroundColor: isUser ? "#228be6" : "#f1f3f5",
            color: isUser ? "white" : "#212529",
            wordBreak: "break-word",
          }}
        >
          {message.content}
        </Text>
        <Text size="xs" c="dimmed" mt={4} ta={isUser ? "right" : "left"}>
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </Text>
      </Box>
    </Box>
  );
}
