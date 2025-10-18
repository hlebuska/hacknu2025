import { zodResolver } from "@hookform/resolvers/zod";
import {
  ActionIcon,
  Button,
  Card,
  Container,
  Group,
  NumberInput,
  Select,
  Stack,
  Text,
  Textarea,
  TextInput,
} from "@mantine/core";
import {
  ArrowLeft,
  Briefcase,
  Building2,
  DollarSign,
  MapPin,
  Plus,
  X,
} from "lucide-react";
import { Controller, useFieldArray, useForm } from "react-hook-form";
import { z } from "zod";
import { useCreateVacancy } from "../../features/vacancies/api/use-create-vacancy";
import { useNavigate } from "react-router";

const vacancySchema = z.object({
  title: z.string().min(3).max(100),
  description: z.string().min(50).max(2000),
  company: z.string().min(2).max(100),
  location: z.string().min(2).max(100),
  salary_min: z.number().min(0).max(10000000),
  salary_max: z.number().min(0).max(10000000),
  employment_type: z.enum(["full-time", "part-time"]),
  requirements: z
    .array(
      z.object({
        title: z.string().min(1),
        description: z.string().min(1),
      })
    )
    .min(1),
});

type VacancyFormData = z.infer<typeof vacancySchema>;

export default function CreateVacancyPage() {
  const createVacancyMutation = useCreateVacancy();

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<VacancyFormData>({
    resolver: zodResolver(vacancySchema),
    defaultValues: {
      title: "",
      description: "",
      company: "",
      location: "",
      salary_min: 0,
      salary_max: 0,
      employment_type: "full-time",
      requirements: [{ title: "", description: "" }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "requirements",
  });

  const onFormSubmit = (data: VacancyFormData) => {
    // Add location to requirements before submission
    const submissionData = {
      ...data,
      requirements: {
        location: data.location,
        ...data.requirements.reduce((acc, req) => {
          acc[req.title] = req.description;
          return acc;
        }, {} as Record<string, string>),
      },
    };

    // Use the mutation to create vacancy
    createVacancyMutation.mutate(submissionData, {
      onSuccess: () => {
        console.log("Vacancy created successfully!");
        reset();
      },
    });
  };

  const navigate = useNavigate();

  const handleBack = () => {
    navigate("/");
  };

  return (
    <Container size="md" py="xl">
      <Group>
        <ActionIcon variant="subtle" size="lg" onClick={handleBack}>
          <ArrowLeft size={20} />
        </ActionIcon>
        <Text size="sm" c="dimmed">
          Back to Jobs
        </Text>
      </Group>
      <Stack gap="lg">
        <div>
          <Text size="xl" fw={700}>
            Create New Vacancy
          </Text>
          <Text size="sm" c="dimmed">
            Fill in the details below
          </Text>
        </div>

        <Card shadow="sm" padding="lg" withBorder>
          <form onSubmit={handleSubmit(onFormSubmit)}>
            <Stack gap="md">
              <Controller
                name="title"
                control={control}
                render={({ field }) => (
                  <TextInput
                    label="Job Title"
                    placeholder="Senior Software Engineer"
                    leftSection={<Briefcase size={16} />}
                    error={errors.title?.message}
                    {...field}
                  />
                )}
              />

              <Group grow>
                <Controller
                  name="company"
                  control={control}
                  render={({ field }) => (
                    <TextInput
                      label="Company"
                      leftSection={<Building2 size={16} />}
                      error={errors.company?.message}
                      {...field}
                    />
                  )}
                />
                <Controller
                  name="location"
                  control={control}
                  render={({ field }) => (
                    <TextInput
                      label="Location"
                      leftSection={<MapPin size={16} />}
                      error={errors.location?.message}
                      {...field}
                    />
                  )}
                />
              </Group>

              <Group grow>
                <Controller
                  name="salary_min"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Min Salary"
                      leftSection={<DollarSign size={16} />}
                      error={errors.salary_min?.message}
                      thousandSeparator=","
                      {...field}
                    />
                  )}
                />
                <Controller
                  name="salary_max"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Max Salary"
                      leftSection={<DollarSign size={16} />}
                      error={errors.salary_max?.message}
                      thousandSeparator=","
                      {...field}
                    />
                  )}
                />
              </Group>

              <Controller
                name="employment_type"
                control={control}
                render={({ field }) => (
                  <Select
                    label="Employment Type"
                    data={[
                      { value: "full-time", label: "Full-time" },
                      { value: "part-time", label: "Part-time" },
                    ]}
                    error={errors.employment_type?.message}
                    {...field}
                  />
                )}
              />

              <Controller
                name="description"
                control={control}
                render={({ field }) => (
                  <Textarea
                    label="Description"
                    placeholder="Job description..."
                    error={errors.description?.message}
                    minRows={4}
                    {...field}
                  />
                )}
              />

              {/* Requirements Section */}
              <div>
                <Group justify="space-between" mb="sm">
                  <Text size="sm" fw={500}>
                    Requirements
                  </Text>
                  <Button
                    size="xs"
                    variant="light"
                    leftSection={<Plus size={14} />}
                    onClick={() => append({ title: "", description: "" })}
                  >
                    Add Requirement
                  </Button>
                </Group>

                <Stack gap="sm">
                  {fields.map((field, index) => (
                    <Card key={field.id} withBorder padding="sm">
                      <Stack gap="xs">
                        <Group justify="space-between" align="center">
                          <Text size="xs" c="dimmed">
                            Requirement {index + 1}
                          </Text>
                          {fields.length > 1 && (
                            <ActionIcon
                              size="sm"
                              color="red"
                              variant="subtle"
                              onClick={() => remove(index)}
                            >
                              <X size={14} />
                            </ActionIcon>
                          )}
                        </Group>

                        <Group grow>
                          <Controller
                            name={`requirements.${index}.title`}
                            control={control}
                            render={({ field }) => (
                              <TextInput
                                placeholder="Requirement title"
                                size="sm"
                                error={
                                  errors.requirements?.[index]?.title?.message
                                }
                                {...field}
                              />
                            )}
                          />
                          <Controller
                            name={`requirements.${index}.description`}
                            control={control}
                            render={({ field }) => (
                              <TextInput
                                placeholder="Requirement description"
                                size="sm"
                                error={
                                  errors.requirements?.[index]?.description
                                    ?.message
                                }
                                {...field}
                              />
                            )}
                          />
                        </Group>
                      </Stack>
                    </Card>
                  ))}
                </Stack>
                {errors.requirements && (
                  <Text size="sm" c="red">
                    {errors.requirements.message}
                  </Text>
                )}
              </div>

              <Group justify="flex-end" mt="lg">
                <Button variant="outline" onClick={() => reset()}>
                  Reset
                </Button>
                <Button type="submit" color="green">
                  Create Vacancy
                </Button>
              </Group>
            </Stack>
          </form>
        </Card>
      </Stack>
    </Container>
  );
}
