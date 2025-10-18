import { Box, Text } from "@mantine/core";

export function ChatHeader() {
  return (
    <Box
      style={{
        padding: "16px 20px",
        borderBottom: "1px solid #e9ecef",
        backgroundColor: "white",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}
    >
      <Box>
        <Text fw={600} size="lg">
          AI Assistant
        </Text>
        <Text size="xs" c="dimmed">
          Always here to help
        </Text>
      </Box>
    </Box>
  );
}
