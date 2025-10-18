import { useMutation } from "@tanstack/react-query";
import { createVacancy } from "../../vacancy/api/vacancies-api";

export const useCreateVacancy = () => {
  return useMutation({
    mutationFn: (vacancyData: any) => createVacancy(vacancyData),
    onSuccess: () => {
      console.log("Vacancy created successfully!");
    },
    onError: (error) => {
      console.error("Failed to create vacancy:", error);
    },
  });
};
