import { zodResolver } from "@hookform/resolvers/zod";
import {
  Button,
  FileInput,
  Group,
  Modal,
  Stack,
  Text,
  TextInput,
} from "@mantine/core";
import { FileText, Mail, Upload, User } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { useSubmitApplication } from "./api/use-submit-application";

// Updated schema without phone
const applicationSchema = z.object({
  firstName: z
    .string()
    .min(2, "First name must have at least 2 characters")
    .max(50, "First name must be less than 50 characters"),
  lastName: z
    .string()
    .min(2, "Last name must have at least 2 characters")
    .max(50, "Last name must be less than 50 characters"),
  email: z
    .string()
    .email("Please enter a valid email address")
    .min(1, "Email is required"),
  resume: z
    .instanceof(File, { message: "Resume is required" })
    .refine(
      (file) => file.size <= 5 * 1024 * 1024,
      "File size must be less than 5MB"
    )
    .refine(
      (file) =>
        [
          "application/pdf",
          "application/msword",
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ].includes(file.type),
      "Only PDF, DOC, and DOCX files are allowed"
    ),
});

type ApplicationFormData = z.infer<typeof applicationSchema>;

interface FormModalProps {
  opened: boolean;
  onClose: () => void;
  jobTitle?: string;
  companyName?: string;
  vacancyId: string;
  onSubmit?: () => void;
}

export function FormModal({
  opened,
  onClose,
  jobTitle = "Software Engineer",
  companyName = "TechCorp",
  vacancyId,
  onSubmit,
}: FormModalProps) {
  const handleSuccess = () => {
    console.log("Application submitted successfully!");
    onClose();
    onSubmit && onSubmit();
  };

  const handleError = (error: any) => {
    console.error("Failed to submit application:", error);
  };

  const submitApplicationMutation = useSubmitApplication({
    onSuccess: handleSuccess,
    onError: handleError,
  });

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ApplicationFormData>({
    resolver: zodResolver(applicationSchema),
    mode: "onChange",
    defaultValues: {
      firstName: "",
      lastName: "",
      email: "",
      resume: undefined as any,
    },
  });

  const onFormSubmit = (data: ApplicationFormData) => {
    const submissionData = {
      vacancy_id: vacancyId,
      first_name: data.firstName,
      last_name: data.lastName,
      email: data.email,
      resume: data.resume,
    };

    submitApplicationMutation.mutate(submissionData, {
      onSuccess: () => {
        onClose();
        reset();
      },
    });
    onSubmit && onSubmit();
  };

  const handleClose = () => {
    onClose();
    reset();
  };

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title={
        <Text size="lg" fw={600}>
          Apply for {jobTitle} at {companyName}
        </Text>
      }
      size="xl"
      centered
      overlayProps={{
        backgroundOpacity: 0.55,
        blur: 3,
      }}
    >
      <form onSubmit={handleSubmit(onFormSubmit)}>
        <Stack gap="36px" p="16px">
          <div>
            <Text size="md" fw={500} c="#18191c" mb="md">
              Personal Information
            </Text>
            <Stack gap="md">
              <Group grow>
                <Controller
                  name="firstName"
                  control={control}
                  render={({ field }) => (
                    <TextInput
                      label="First Name"
                      placeholder="Enter your first name"
                      leftSection={<User size={16} />}
                      error={errors.firstName?.message}
                      required
                      {...field}
                    />
                  )}
                />
                <Controller
                  name="lastName"
                  control={control}
                  render={({ field }) => (
                    <TextInput
                      label="Last Name"
                      placeholder="Enter your last name"
                      leftSection={<User size={16} />}
                      error={errors.lastName?.message}
                      required
                      {...field}
                    />
                  )}
                />
              </Group>
              <Controller
                name="email"
                control={control}
                render={({ field }) => (
                  <TextInput
                    label="Email Address"
                    placeholder="your.email@example.com"
                    leftSection={<Mail size={16} />}
                    error={errors.email?.message}
                    required
                    {...field}
                  />
                )}
              />
            </Stack>
          </div>

          <div>
            <Text size="md" fw={500} c="#18191c" mb="md">
              Professional Information
            </Text>
            <Controller
              name="resume"
              control={control}
              render={({ field: { onChange, value, ...field } }) => (
                <FileInput
                  size="md"
                  label="Resume/CV"
                  placeholder="Upload your resume (PDF, DOC, DOCX)"
                  leftSection={<FileText size={16} />}
                  accept=".pdf,.doc,.docx"
                  error={errors.resume?.message}
                  required
                  onChange={onChange}
                  value={value}
                  {...field}
                />
              )}
            />
          </div>

          <Group justify="space-between" mt="xl">
            <Button variant="outline" onClick={handleClose} size="md">
              Cancel
            </Button>
            <Button
              type="submit"
              size="md"
              leftSection={<Upload size={16} />}
              loading={submitApplicationMutation.isPending}
            >
              Submit Application
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
