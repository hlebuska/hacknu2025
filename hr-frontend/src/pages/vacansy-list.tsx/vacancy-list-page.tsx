import { Button, Container, Loader, Stack, Text } from "@mantine/core";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useNavigate } from "react-router";
import { getVacancies } from "../../features/vacancy/api/vacancies-api";
import type { Job } from "../../features/vacancy/model/types";
import { JobCard } from "../../features/vacancy/ui/job-card";

export default function VacanciesPage() {
  const navigate = useNavigate();

  const {
    data: vacancies,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["vacancies"],
    queryFn: getVacancies,
    staleTime: 5 * 60 * 1000,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  const jobsData: Job[] = vacancies || [];

  console.log(jobsData);

  return (
    <Container style={{ minHeight: "100vh" }}>
      <div className="min-h-screen bg-background">
        <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="mb-8 flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-foreground">
              Latest Positions
            </h2>
            <div className="flex items-center gap-2">
              {isLoading && <Loader size="sm" />}
              <p className="text-muted-foreground">
                {jobsData.length} open positions
              </p>
            </div>
          </div>
          {isLoading && !vacancies && (
            <div className="flex justify-center items-center py-12">
              <Stack align="center" gap="md">
                <Loader size="lg" />
                <Text c="dimmed">Loading job opportunities...</Text>
              </Stack>
            </div>
          )}
          {isError && !jobsData.length && (
            <div className="flex justify-center items-center py-12">
              <Stack align="center" gap="md">
                <AlertTriangle size={48} color="#fa5252" />
                <Text size="lg" fw={500}>
                  Failed to Load Jobs
                </Text>
                <Text c="dimmed" ta="center">
                  We couldn't fetch the latest job postings. Please check your
                  connection and try again.
                </Text>
                <button
                  onClick={() => refetch()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Retry
                </button>
              </Stack>
            </div>
          )}
          {jobsData.length > 0 && jobsData ? (
            <div className="grid gap-6 sm:grid-cols-1 md:grid-cols-2 ">
              {jobsData?.map((job: Job) => (
                <JobCard
                  key={job.id}
                  title={job.title}
                  company={job.company}
                  location={job.location}
                  employmentType={job.title}
                  salaryLow={job.salary_min}
                  salaryHigh={job.salary_max}
                  onBookmark={() => console.log(`Bookmarked ${job.title}`)}
                  onClick={() => navigate(`/vacancy/${job.id}`)}
                />
              ))}
            </div>
          ) : (
            !isLoading && (
              <Text
                style={{ display: "flex", justifyContent: "center" }}
                c="dimmed"
              >
                No job postings available
              </Text>
            )
          )}
        </main>
        <Button
          style={{
            display: "flex",
            justifyContent: "center",
            width: "100%",
            maxWidth: "200px",
            margin: "0 auto 2rem auto",
          }}
          onClick={() => navigate("/create")}
        >
          Post a Job
        </Button>
      </div>
    </Container>
  );
}
