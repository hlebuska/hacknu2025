import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Container,
  Divider,
  Group,
  Loader,
  Stack,
  Text,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { ArrowLeft, Building2, Clock, DollarSign, Trash2 } from "lucide-react";
import { useNavigate, useParams } from "react-router";

import { useVacancy } from "../../features/vacancy/api/use-vacancy";
import { formatPostedDate } from "../../utils/date-formatter";

export function VacancyInfoPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [opened, { open }] = useDisclosure(false);

  const { data: job, isLoading, error } = useVacancy(id!);

  const handleBack = () => {
    navigate("/");
  };

  console.log("Job Data:", opened);

  if (isLoading) {
    return (
      <Container style={{ minHeight: "100vh" }}>
        <Stack align="center" justify="center" style={{ minHeight: "50vh" }}>
          <Loader size="lg" />
          <Text size="lg" c="dimmed">
            Loading job details...
          </Text>
        </Stack>
      </Container>
    );
  }

  if (error || !job) {
    return (
      <Container style={{ minHeight: "100vh" }}>
        <Stack align="center" justify="center" style={{ minHeight: "50vh" }}>
          <Text size="xl" c="dimmed">
            Job not found
          </Text>
          <Button onClick={handleBack}>Back to Jobs</Button>
        </Stack>
      </Container>
    );
  }

  return (
    <Container size="md" py="xl">
      <Stack gap="lg">
        <Group>
          <ActionIcon variant="subtle" size="lg" onClick={handleBack}>
            <ArrowLeft size={20} />
          </ActionIcon>
          <Text size="sm" c="dimmed">
            Back to Jobs
          </Text>
        </Group>

        <Card shadow="sm" padding="xl" radius="md" withBorder>
          <Stack gap="lg">
            {/* Header */}
            <div>
              <Text size="xl" fw={700} mb="xs">
                {job.title}
              </Text>
              <Group gap="md" mb="md">
                <Group gap="xs">
                  <Building2 size={16} color="#767f8c" />
                  <Text size="md" fw={500} c="#0ba02c">
                    {job.company}
                  </Text>
                </Group>
                <Group gap="xs">
                  <Clock size={16} color="#767f8c" />
                  <Text size="sm" c="#767f8c">
                    {formatPostedDate(job.created_at)}
                  </Text>
                </Group>
              </Group>

              <Group gap="md">
                <Badge
                  color="green"
                  variant="light"
                  size="md"
                  styles={{
                    root: {
                      backgroundColor: "#e7f6ea",
                      color: "#0ba02c",
                      textTransform: "uppercase",
                      fontWeight: 600,
                    },
                  }}
                >
                  {job.employment_type}
                </Badge>
                <Group gap="xs">
                  <DollarSign size={16} color="#767f8c" />
                  <Text size="sm" fw={500}>
                    {job.salary_min} - {job.salary_max} USD/year
                  </Text>
                </Group>
              </Group>
            </div>

            <Divider />

            {/* Description */}
            <div>
              <Text size="lg" fw={600} mb="sm">
                Description
              </Text>
              <Text size="sm" c="#4f4f4f" style={{ lineHeight: 1.6 }}>
                {job.description}
              </Text>
            </div>

            <Divider />

            {/* Requirements */}
            <div>
              <Text size="lg" fw={600} mb="sm">
                Requirements
              </Text>
              <Stack gap="xs">
                {job?.requirements &&
                  typeof job.requirements === "object" &&
                  Object.entries(job.requirements).map(([key, value]) => (
                    <Group key={key} gap="xs" align="center">
                      <div
                        style={{
                          width: "6px",
                          height: "6px",
                          borderRadius: "50%",
                          backgroundColor: "#0ba02c",
                          flexShrink: 0,
                        }}
                      />
                      <Text size="sm" c="#4f4f4f">
                        <Text component="span" fw={500} c="#18191c">
                          {key
                            .replace(/_/g, " ")
                            .replace(/\b\w/g, (l) => l.toUpperCase())}
                          :
                        </Text>{" "}
                        {typeof value === "boolean"
                          ? value
                            ? "Yes"
                            : "No"
                          : String(value)}
                      </Text>
                    </Group>
                  ))}
              </Stack>
            </div>

            <Divider />

            {/* Delete Button */}
            <Button
              size="lg"
              radius="md"
              color="red"
              leftSection={<Trash2 size={16} />}
              onClick={open}
              style={{ alignSelf: "flex-start" }}
            >
              Delete Job
            </Button>
          </Stack>
        </Card>
      </Stack>
    </Container>
  );
}
