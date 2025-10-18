import { useQuery } from "@tanstack/react-query";
import { getVacancyById } from "./vacancies-api";

export const useVacancy = (id: string) => {
  return useQuery({
    queryKey: ["vacancy", id],
    queryFn: () => getVacancyById(id),
    enabled: !!id,
  });
};
