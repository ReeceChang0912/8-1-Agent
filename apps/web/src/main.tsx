import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import WorkbenchPage from './pages/WorkbenchPage'
import ChatPage from './pages/ChatPage'
import MembersPage from './pages/MembersPage'
import SchedulePage from './pages/SchedulePage'
import ShoppingPage from './pages/ShoppingPage'
import PhotosPage from './pages/PhotosPage'
import KnowledgePage from './pages/KnowledgePage'
import MemoryPage from './pages/MemoryPage'
import SkillsPage from './pages/SkillsPage'
import SmartHomePage from './pages/SmartHomePage'
import MCPPage from './pages/MCPPage'
import StatsPage from './pages/StatsPage'
import NotificationsPage from './pages/NotificationsPage'
import FinancePage from './pages/FinancePage'
import ModulesPage from './pages/ModulesPage'
import WeddingPage from './pages/WeddingPage'
import InsurancePage from './pages/InsurancePage'
import VehiclePage from './pages/VehiclePage'
import FitnessPage from './pages/FitnessPage'
import DocumentsPage from './pages/DocumentsPage'
import HousingPage from './pages/HousingPage'
import './styles/responsive.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ConfigProvider locale={zhCN}>
        <Routes>
          <Route path="/login" element={<Navigate to="/" replace />} />
          <Route path="/" element={<App />}>
            <Route index element={<WorkbenchPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="members" element={<MembersPage />} />
            <Route path="schedule" element={<SchedulePage />} />
            <Route path="shopping" element={<ShoppingPage />} />
            <Route path="photos" element={<PhotosPage />} />
            <Route path="knowledge" element={<KnowledgePage />} />
            <Route path="memory" element={<MemoryPage />} />
            <Route path="skills" element={<SkillsPage />} />
            <Route path="smarthome" element={<SmartHomePage />} />
            <Route path="mcp" element={<MCPPage />} />
            <Route path="stats" element={<StatsPage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="finance" element={<FinancePage />} />
            <Route path="modules" element={<ModulesPage />} />
            <Route path="modules/wedding" element={<WeddingPage />} />
            <Route path="modules/insurance" element={<InsurancePage />} />
            <Route path="modules/vehicle" element={<VehiclePage />} />
            <Route path="modules/fitness" element={<FitnessPage />} />
            <Route path="modules/documents" element={<DocumentsPage />} />
            <Route path="modules/housing" element={<HousingPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </ConfigProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
