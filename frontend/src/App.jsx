import React, { useState, useEffect, lazy, Suspense } from 'react';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import ErrorBoundary from './components/common/ErrorBoundary';
import ClinicalLoadingSkeleton from './components/common/ClinicalLoadingSkeleton';
import { apiClient } from './api/client';

// 7 Unified Primary Clinical Modules - Dynamic Code-Split Lazy Imports
const DashboardView = lazy(() => import('./components/dashboard/DashboardView'));
const NewAnalysisView = lazy(() => import('./components/analysis/NewAnalysisView'));
const PatientReportsView = lazy(() => import('./components/reports/PatientReportsView'));
const AIAgentWorkstationView = lazy(() => import('./components/agent/AIAgentWorkstationView'));
const FindSpecialistView = lazy(() => import('./components/specialist/FindSpecialistView'));
const AIAssistantView = lazy(() => import('./components/assistant/AIAssistantView'));
const AboutView = lazy(() => import('./components/about/AboutView'));

// Modals - Code-Split Lazy Imports
const ClinicalReportModal = lazy(() => import('./components/modals/ClinicalReportModal'));
const HospitalAuthModal = lazy(() => import('./components/auth/HospitalAuthModal'));

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [centers, setCenters] = useState([]);
  const [selectedCenter, setSelectedCenter] = useState(null);
  const [screenings, setScreenings] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [activeSessionDetail, setActiveSessionDetail] = useState(null);
  const [analyticsStats, setAnalyticsStats] = useState(null);
  const [isSeeding, setIsSeeding] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  // Hospital Authentication State
  const [hospital, setHospital] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Modals state
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportSession, setReportSession] = useState(null);

  // Load initial data and verify hospital session
  const loadInitialData = async () => {
    try {
      const savedToken = localStorage.getItem('mindhue_token');
      const savedHosp = localStorage.getItem('mindhue_hospital');

      if (savedToken && savedHosp) {
        try {
          setHospital(JSON.parse(savedHosp));
        } catch (e) {
          console.error('Error parsing stored hospital profile:', e);
        }
      } else {
        // Fetch default active hospital account
        apiClient.getHospitalMe()
          .then(res => {
            if (res.authenticated && res.hospital) {
              setHospital(res.hospital);
            }
          })
          .catch(() => {});
      }

      const [centersData, screeningsData, statsData] = await Promise.all([
        apiClient.getCenters(),
        apiClient.getScreenings(),
        apiClient.getAnalyticsOverview()
      ]);

      setCenters(centersData || []);
      if (centersData && centersData.length > 0) {
        setSelectedCenter(centersData[0]);
      }

      setScreenings(screeningsData || []);
      if (screeningsData && screeningsData.length > 0) {
        setActiveSessionId(screeningsData[0].id);
      }

      setAnalyticsStats(statsData || null);
    } catch (err) {
      console.error('Error loading initial clinical telemetry:', err);
    } finally {
      setIsInitialLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // Fetch deep session details when activeSessionId changes
  useEffect(() => {
    if (activeSessionId) {
      apiClient.getScreeningDetail(activeSessionId)
        .then(data => setActiveSessionDetail(data))
        .catch(err => console.error('Failed to load session details:', err));
    }
  }, [activeSessionId]);

  // Handlers for Hospital Auth
  const handleLoginSuccess = (hospData, token) => {
    setHospital(hospData);
    localStorage.setItem('mindhue_token', token);
    localStorage.setItem('mindhue_hospital', JSON.stringify(hospData));
    loadInitialData();
  };

  const handleLogoutHospital = () => {
    setHospital(null);
    localStorage.removeItem('mindhue_token');
    localStorage.removeItem('mindhue_hospital');
  };

  // Handlers for screening workflow
  const handleSelectSession = (sessionId) => {
    setActiveSessionId(sessionId);
    setActiveTab('ai-agent');
  };

  const handleViewReport = async (sessionId) => {
    try {
      const detail = await apiClient.getScreeningDetail(sessionId);
      setReportSession(detail);
      setIsReportModalOpen(true);
    } catch (err) {
      console.error('Failed to view clinical report:', err);
    }
  };

  const handleCreatePatient = async (patientData) => {
    try {
      // Clean district center ID (avoid empty string which can fail validation)
      const centerId = patientData.district_center || selectedCenter?.id || centers?.[0]?.id || null;

      // Generate collision-free MRN
      const uniqueSuffix = `${Date.now().toString().slice(-4)}${Math.floor(100 + Math.random() * 900)}`;
      const mrn = patientData.mrn && !patientData.mrn.match(/^MRN-2026-\d{3}$/)
        ? patientData.mrn
        : `MRN-2026-${uniqueSuffix}`;

      const newPatient = await apiClient.createPatient({
        ...patientData,
        mrn,
        district_center: centerId,
        hospital_account: hospital?.id || null
      });

      const sessionCode = `SESS-${newPatient.mrn}`;
      const newSession = await apiClient.createScreeningSession({
        patient: newPatient.id,
        session_code: sessionCode,
        district_center: newPatient.district_center || centerId,
        hospital_account: hospital?.id || null
      });

      const updatedScreenings = await apiClient.getScreenings();
      setScreenings(updatedScreenings);
      return newSession;
    } catch (err) {
      console.error('Error creating patient intake session:', err);
      throw err;
    }
  };

  const handleValidateSession = async (sessionId, validationData) => {
    const updated = await apiClient.validateSession(sessionId, validationData);
    setActiveSessionDetail(updated);

    const [updatedScreenings, updatedStats] = await Promise.all([
      apiClient.getScreenings(),
      apiClient.getAnalyticsOverview()
    ]);
    setScreenings(updatedScreenings);
    setAnalyticsStats(updatedStats);
  };

  const handleSeedBenchmark = async () => {
    setIsSeeding(true);
    try {
      await apiClient.seedBenchmark();
      await loadInitialData();
    } catch (err) {
      console.error('Error seeding benchmark dataset:', err);
    } finally {
      setIsSeeding(false);
    }
  };

  const pendingCount = screenings.filter(s => s.status === 'AI_GRADED' || s.status === 'PENDING_AI').length;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-[#005eb8] selection:text-white">
      
      {/* Top subtle clinical synchronization progress bar */}
      {isInitialLoading && (
        <div className="h-1 w-full bg-blue-100 overflow-hidden fixed top-0 left-0 z-50">
          <div className="h-full bg-[#005eb8] animate-pulse w-full origin-left" />
        </div>
      )}

      {/* Official WHO Header */}
      <Header
        centers={centers}
        selectedCenter={selectedCenter}
        onSelectCenter={setSelectedCenter}
        stats={analyticsStats}
        onSeedData={handleSeedBenchmark}
        isSeeding={isSeeding}
        hospital={hospital}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
        onLogoutHospital={handleLogoutHospital}
      />

      {/* Main Workspace Layout */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        
        {/* Navigation Sidebar: 7 Core Modules */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          pendingReviewCount={pendingCount}
          hospital={hospital}
          onOpenAuthModal={() => setIsAuthModalOpen(true)}
        />

        {/* Tab Content Area Protected by ErrorBoundary & Suspense */}
        <main className="flex-1 p-4 lg:p-6 overflow-y-auto max-h-[calc(100vh-95px)] bg-slate-50">
          <ErrorBoundary>
            <Suspense fallback={<ClinicalLoadingSkeleton />}>
              
              {/* 1. DASHBOARD */}
              {activeTab === 'dashboard' && (
                <DashboardView
                  stats={analyticsStats}
                  screenings={screenings}
                  hospital={hospital}
                  onNavigate={setActiveTab}
                  onSelectSession={handleSelectSession}
                  onOpenReport={handleViewReport}
                />
              )}

              {/* 2. NEW ANALYSIS */}
              {activeTab === 'new-analysis' && (
                <NewAnalysisView
                  centers={centers}
                  selectedCenter={selectedCenter}
                  hospital={hospital}
                  onSubmitNewPatient={handleCreatePatient}
                  onAnalysisComplete={(sessionId) => {
                    if (sessionId) setActiveSessionId(sessionId);
                    setActiveTab('ai-agent');
                  }}
                />
              )}

              {/* 3. PATIENT REPORTS */}
              {activeTab === 'patient-reports' && (
                <PatientReportsView
                  screenings={screenings}
                  onSelectSession={handleSelectSession}
                  onViewReport={handleViewReport}
                />
              )}

              {/* 4. AI ANALYSIS AGENT */}
              {activeTab === 'ai-agent' && (
                <AIAgentWorkstationView
                  session={activeSessionDetail || screenings[0]}
                  onBack={() => setActiveTab('dashboard')}
                  onValidate={handleValidateSession}
                  onViewReport={handleViewReport}
                  onRunSimulation={apiClient.runSimulation}
                />
              )}

              {/* 5. FIND SPECIALIZATION */}
              {activeTab === 'find-specialist' && (
                <FindSpecialistView
                  hospital={hospital}
                />
              )}

              {/* 6. AI ASSISTANT */}
              {activeTab === 'ai-assistant' && (
                <AIAssistantView />
              )}

              {/* 7. ABOUT */}
              {activeTab === 'about' && (
                <AboutView />
              )}

            </Suspense>
          </ErrorBoundary>
        </main>

      </div>

      {/* Code-Split Modals */}
      <Suspense fallback={null}>
        {isAuthModalOpen && (
          <HospitalAuthModal
            isOpen={isAuthModalOpen}
            onClose={() => setIsAuthModalOpen(false)}
            onLoginSuccess={handleLoginSuccess}
          />
        )}

        {isReportModalOpen && (
          <ClinicalReportModal
            isOpen={isReportModalOpen}
            onClose={() => setIsReportModalOpen(false)}
            session={reportSession}
          />
        )}
      </Suspense>

    </div>
  );
}
