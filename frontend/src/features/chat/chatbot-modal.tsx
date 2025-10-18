import { Chatbot } from "../widget/chat";
import { Modal, Button, Box } from "@mantine/core";
import { MessageCircle } from "lucide-react";
import { useState } from "react";

interface ChatbotModalProps {
  vacancyId?: string;
  applicationId?: string;
  opened: boolean;
  onClose: () => void;
}

export function ChatbotModal({
  vacancyId,
  applicationId,
  opened,
  onClose,
}: ChatbotModalProps) {
  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="AI Recruitment Assistant"
      size="lg"
      styles={{
        body: {
          padding: 0,
          height: "70vh",
        },
      }}
    >
      <Box style={{ height: "100%" }}>
        <Chatbot
          vacancyId={vacancyId}
          applicationId={applicationId}
        />
      </Box>
    </Modal>
  );
}

interface ChatbotButtonProps {
  vacancyId?: string;
  applicationId?: string;
}

export function ChatbotButton({
  vacancyId,
  applicationId,
}: ChatbotButtonProps) {
  const [opened, setOpened] = useState(false);

  return (
    <>
      <Button
        leftSection={<MessageCircle size={18} />}
        onClick={() => setOpened(true)}
        variant="light"
      >
        Ask AI Assistant
      </Button>
      <ChatbotModal
        vacancyId={vacancyId}
        applicationId={applicationId}
        opened={opened}
        onClose={() => setOpened(false)}
      />
    </>
  );
}
