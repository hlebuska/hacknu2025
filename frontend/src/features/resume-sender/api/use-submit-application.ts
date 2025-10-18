import { useMutation } from "@tanstack/react-query";
import { axiosClient } from "../../vacancies/api/vacancies-api";

interface ApplicationData {
  vacancy_id: string;
  first_name: string;
  last_name: string;
  email: string;
  resume: File;
}

const submitApplication = async (data: ApplicationData): Promise<any> => {
  const formData = new FormData();

  formData.append("vacancy_id", data.vacancy_id);
  formData.append("first_name", data.first_name);
  formData.append("last_name", data.last_name);
  formData.append("email", data.email);
  formData.append("resume", data.resume);
  console.log("Submitting application with data:", data);

  const response = await axiosClient.post("/applications", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
};

interface UseSubmitApplicationArgs {
  onSuccess?: () => void;
  onError?: (error: any) => void;
}

export const useSubmitApplication = ({
  onSuccess,
  onError,
}: UseSubmitApplicationArgs) => {
  return useMutation({
    mutationFn: submitApplication,
    onSuccess: () => {
      onSuccess && onSuccess();
    },
    onError: (error) => {
      onError && onError(error);
    },
  });
};
