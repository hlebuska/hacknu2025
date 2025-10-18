import { Chatbot } from "./features/chat/ui/chatbot";

const applicationData = {
  id: "a355b545-644d-49ac-afeb-853d50d61eb2",
  vacancy_id: "5926b170-8c04-4785-8438-94c5c4236d80",
  first_name: "Gleb",
  last_name: "Vassyutinskiy",
  email: "g.v.vass@gmail.com",
  resume_pdf: "uploads/resumes/4bd87715-35c3-448a-8b5c-5bd6172bd2a1.pdf",
  resume_parsed: null,
  matching_score: 50,
  matching_sections: {
    requirements: [
      {
        vacancy_req: "location: Almaty, Kazakhstan",
        user_req_data: "Астана, Казахстан",
        match_percent: 60,
      },
      {
        vacancy_req: "Experience in React: > 3 years",
        user_req_data:
          "Разработал клиентскую часть MVP одностраничного адаптивного приложения (SPA) с использованием React.",
        match_percent: 40,
      },
    ],
    FIT_SCORE: 50,
  },
};

function App() {
  return <Chatbot applicationId={applicationData.id} />;
}

export default App;
