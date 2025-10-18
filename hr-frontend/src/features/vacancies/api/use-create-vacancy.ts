import { useMutation } from "@tanstack/react-query";
import type { Job } from "../../vacancy/model/types";
import { createVacancy } from "../../vacancy/api/vacancies-api";

export const useCreateVacancy = () => {
  return useMutation({
    mutationFn: (vacancyData: Omit<Job, "id" | "created_at" | "updated_at">) =>
      createVacancy(vacancyData),
    onSuccess: () => {
      console.log("Vacancy created successfully!");
    },
    onError: (error) => {
      console.error("Failed to create vacancy:", error);
    },
  });
};
