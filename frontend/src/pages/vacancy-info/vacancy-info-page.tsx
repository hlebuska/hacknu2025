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
import { ArrowLeft, Building2, Clock, DollarSign, MapPin } from "lucide-react";
import { useNavigate, useParams } from "react-router";
import { FormModal } from "../../features/resume-sender/form-modal";
import { useWidget } from "../../features/widget/api/use-widget";
import { Widget } from "../../features/widget/ui/widget";
import { useVacancy } from "../../features/vacancies/api/use-vacancy";
import { formatPostedDate } from "../../utils/date-formatter";

export function VacancyInfoPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [opened, { open, close }] = useDisclosure(false);
  const { widgetOpen, setWidgetOpen } = useWidget();

  const { data: job, isLoading, error } = useVacancy(id!);

  const handleBack = () => {
    navigate("/");
  };

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
    <>
      <FormModal
        opened={opened}
        onClose={close}
        jobTitle={job.title}
        companyName={job.company}
        onSubmit={() => setWidgetOpen(true)}
      />
      {widgetOpen && <Widget />}
      <Container
        size="lg"
        style={{
          minHeight: "100vh",
          paddingTop: "2rem",
          paddingBottom: "2rem",
        }}
      >
        <Stack gap="xl">
          <Group>
            <ActionIcon variant="subtle" size="lg" onClick={handleBack}>
              <ArrowLeft size={20} />
            </ActionIcon>
            <Text size="sm" c="dimmed">
              Back to Jobs
            </Text>
          </Group>

          <Card shadow="sm" padding="xl" radius="md" withBorder>
            <Stack gap="md">
              <Group justify="space-between" align="flex-start">
                <Stack gap="xs" style={{ flex: 1 }}>
                  <Text size="xl" fw={700} c="#18191c">
                    {job.title}
                  </Text>
                  <Group gap="md">
                    <Group gap="xs">
                      <Building2 size={16} color="#767f8c" />
                      <Text size="md" fw={500} c="#0ba02c">
                        {job.company}
                      </Text>
                    </Group>
                    <Group gap="xs">
                      <MapPin size={16} color="#767f8c" />
                      <Text size="sm" c="#767f8c">
                        {job.location}
                      </Text>
                    </Group>
                  </Group>
                </Stack>
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

                <Group gap="xs">
                  <Clock size={16} color="#767f8c" />
                  <Text size="sm" c="#767f8c">
                    {formatPostedDate(job.created_at)}
                  </Text>
                </Group>
              </Group>

              <Group justify="space-between" mt="md">
                <Button
                  size="lg"
                  radius="md"
                  style={{ flex: 1, maxWidth: "200px" }}
                  onClick={open}
                >
                  Apply Now
                </Button>
                <Text size="sm" c="#767f8c"></Text>
              </Group>
            </Stack>
          </Card>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "2fr 1fr",
              gap: "2rem",
              alignItems: "start",
            }}
          >
            <div
              style={{
                display: "grid",
                gap: "1.5rem",
              }}
            >
              <Card shadow="sm" padding="xl" radius="md" withBorder>
                <Stack gap="md">
                  <Text size="lg" fw={600} c="#18191c">
                    Job Description
                  </Text>
                  <Text size="sm" c="#4f4f4f" style={{ lineHeight: 1.6 }}>
                    {job.description}
                  </Text>
                </Stack>
              </Card>

              {/* Requirements Card */}
              <Card shadow="sm" padding="xl" radius="md" withBorder>
                <Stack gap="md">
                  <Text size="lg" fw={600} c="#18191c">
                    Requirements
                  </Text>
                  <div
                    style={{
                      display: "grid",
                      gap: "0.5rem",
                    }}
                  >
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
                  </div>
                </Stack>
              </Card>
            </div>

            <div
              style={{
                display: "grid",
                gap: "1rem",
                gridTemplateRows: "max-content",
                position: "sticky",
                top: "2rem",
              }}
            >
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <div
                  style={{
                    display: "grid",
                    gap: "1rem",
                  }}
                >
                  <Text size="md" fw={600} c="#18191c">
                    Quick Apply
                  </Text>
                  <Button fullWidth size="md" radius="md" onClick={open}>
                    Apply Now
                  </Button>
                  <Divider />

                  <div
                    style={{
                      display: "grid",
                      gap: "0.75rem",
                    }}
                  >
                    <div style={{ display: "grid", gap: "0.25rem" }}>
                      <Text size="sm" fw={500} c="#18191c">
                        Job Type
                      </Text>
                      <Text size="sm" c="#767f8c">
                        {job.employment_type}
                      </Text>
                    </div>

                    <div style={{ display: "grid", gap: "0.25rem" }}>
                      <Text size="sm" fw={500} c="#18191c">
                        Requirements
                      </Text>
                      <Text size="sm" c="#767f8c"></Text>
                    </div>

                    <div style={{ display: "grid", gap: "0.25rem" }}>
                      <Text size="sm" fw={500} c="#18191c">
                        Salary
                      </Text>
                      <Text size="sm" c="#767f8c">
                        {job.salary_min} - {job.salary_max} USD/year
                      </Text>
                    </div>

                    <div style={{ display: "grid", gap: "0.25rem" }}>
                      <Text size="sm" fw={500} c="#18191c">
                        Location
                      </Text>
                      <Text size="sm" c="#767f8c">
                        {job.location}
                      </Text>
                    </div>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </Stack>
      </Container>
    </>
  );
}
