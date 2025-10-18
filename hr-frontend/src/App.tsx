import { BrowserRouter, Route, Routes } from "react-router";
import CreateVacancyPage from "./pages/create-vacancy/create-vacancy-page";
import VacanciesPage from "./pages/vacansy-list.tsx/vacancy-list-page";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/create" element={<CreateVacancyPage />}></Route>
        <Route path="/" element={<VacanciesPage />}></Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
