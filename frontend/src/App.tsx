import { BrowserRouter, Route, Routes } from "react-router";
import "./App.css";
import VacanciesPage from "./pages/vacancies/vacancies-page";
import { VacancyInfoPage } from "./pages/vacancy-info/vacancy-info-page";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<VacanciesPage></VacanciesPage>} />
        <Route path="/vacancy/:id" element={<VacancyInfoPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
