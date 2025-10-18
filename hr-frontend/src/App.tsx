import { BrowserRouter, Route, Routes } from "react-router";
import CreateVacancyPage from "./pages/create-vacancy/create-vacancy-page";
import VacanciesPage from "./pages/vacansy-list.tsx/vacancy-list-page";
import { VacancyInfoPage } from "./pages/vacancy-info/vacancy-info-page";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/create" element={<CreateVacancyPage />}></Route>
        <Route path="/" element={<VacanciesPage />}></Route>
        <Route path="/vacancy/:id" element={<VacancyInfoPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
