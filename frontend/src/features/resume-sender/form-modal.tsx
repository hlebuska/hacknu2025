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

// Zod schema for form validation (simplified for essential fields only)
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
  onSubmit?: (data: ApplicationFormData) => void;
}

export function FormModal({
  opened,
  onClose,
  jobTitle = "Software Engineer",
  companyName = "TechCorp",
  onSubmit,
}: FormModalProps) {
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
    console.log("Application submitted:", data);
    if (onSubmit) {
      onSubmit(data);
    }
    onClose();
    reset();
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
      size="50vw"
      centered
      overlayProps={{
        backgroundOpacity: 0.55,
        blur: 3,
      }}
    >
      <form onSubmit={handleSubmit(onFormSubmit)}>
        <Stack gap="36px" p="16px">
          <div className="flex flex-col gap-4">
            <Text size="md" fw={500} c="#18191c">
              Personal Information
            </Text>
            <Group
              grow
              style={{ flexDirection: "row", alignItems: "flex-start" }}
            >
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
          </div>

          <div className="flex flex-col gap-4">
            <Text size="md" fw={500} c="#18191c">
              Professional Information
            </Text>
            <Stack gap="sm">
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
            </Stack>
          </div>

          <Group justify="space-between" mt="xl">
            <Button variant="outline" onClick={handleClose} size="md">
              Cancel
            </Button>
            <Button
              type="submit"
              size="md"
              leftSection={<Upload size={16} />}
              //   disabled={!isValid || !isDirty}
            >
              Submit Application
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}
