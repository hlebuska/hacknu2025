import {
  ActionIcon,
  Badge,
  Box,
  Card,
  Group,
  rem,
  Stack,
  Text,
} from "@mantine/core";
import "@mantine/core/styles.css";
import { MoveDiagonal, PinIcon } from "lucide-react";

interface JobCardProps {
  title?: string;
  company?: string;
  location?: string;
  employmentType?: string;
  salaryLow?: string;
  salaryHigh?: string;
  companyLogo?: string;
  onBookmark?: () => void;
  onClick?: () => void;
}

export function JobCard({
  title = "Front End Developer",
  company = "Mycar.kz",
  location = "Dhaka, Bangladesh",
  employmentType = "Part-time",
  salaryLow,
  salaryHigh,
  companyLogo = "./mycar-logo.svg",
  onBookmark,
  onClick,
}: JobCardProps) {
  return (
    <Card
      shadow="xs"
      padding="xl"
      radius="md"
      withBorder
      style={{ height: "100%", cursor: "pointer" }}
      onClick={onClick}
    >
      <Stack gap="lg">
        {/* Heading Section */}
        <Stack gap={6}>
          <Text size="lg" fw={500} c="#18191c">
            {title}
          </Text>
          <Group gap={8}>
            <Badge
              color="green"
              variant="light"
              size="sm"
              styles={{
                root: {
                  backgroundColor: "#e7f6ea",
                  color: "#0ba02c",
                  textTransform: "uppercase",
                  fontWeight: 600,
                  fontSize: rem(12),
                  letterSpacing: "0.02em",
                },
              }}
            >
              {employmentType}
            </Badge>
            <Text size="sm" c="#767f8c">
              Salary: {salaryLow} - {salaryHigh}
            </Text>
          </Group>
        </Stack>

        {/* Company Section */}
        <Group gap="md" wrap="nowrap">
          <Box
            style={{
              padding: 12,
              borderRadius: 4,
              display: "flex",
              alignItems: "center",
              flex: 1,
              justifyContent: "center",
            }}
          >
            <img className="w-full" src={companyLogo} alt={`${company} Logo`} />
          </Box>

          <Stack gap={4} style={{ flex: 4 }}>
            <Text size="md" fw={500} c="#18191c">
              {company}
            </Text>
            <Group gap={4}>
              <PinIcon size={18} color="#767f8c" />
              <Text size="sm" c="#767f8c">
                {location}
              </Text>
            </Group>
          </Stack>

          <ActionIcon
            variant="subtle"
            color="gray"
            size="lg"
            onClick={onBookmark}
          >
            <MoveDiagonal size={24} color="#c8ccd1" />
          </ActionIcon>
        </Group>
      </Stack>
    </Card>
  );
}
