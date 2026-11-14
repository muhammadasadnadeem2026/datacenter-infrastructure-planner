import { Navigate, Route, Routes } from 'react-router-dom';
import { ToolPage } from './components/calculators/ToolPage';
import { AppLayout } from './components/layouts/AppLayout';
import { TOOLS } from './constants/tools';
import { AIRackPage } from './pages/AIRackPage';
import { CalculatorPage } from './pages/CalculatorPage';
import { MethodologyPage } from './pages/MethodologyPage';
import { ProjectsPage } from './pages/ProjectsPage';
import { ReferencesPage } from './pages/ReferencesPage';
import { SettingsPage } from './pages/SettingsPage';
import { UnitsConverterPage } from './pages/UnitsConverterPage';

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/calculator" replace />} />
        <Route path="/calculator" element={<CalculatorPage />} />
        {TOOLS.map((t) => (
          <Route key={t.id} path={t.path} element={<ToolPage key={t.id} config={t} />} />
        ))}
        <Route path="/tools/units" element={<UnitsConverterPage />} />
        <Route path="/tools/ai-rack" element={<AIRackPage />} />
        <Route path="/methodology" element={<MethodologyPage />} />
        <Route path="/references" element={<ReferencesPage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<p className="text-sm text-slate-600">Page not found.</p>} />
      </Route>
    </Routes>
  );
}
