import React, { useState, useEffect } from 'react';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import PatientTriageView from './components/triage/PatientTriageView';
import FastReviewStudio from './components/workstation/FastReviewStudio';
import RetinalInspector from './components/workstation/RetinalInspector';
import DistrictEpidemiologyDashboard from './components/analytics/DistrictEpidemiologyDashboard';
import SimulinkSimulatorView from './components/simulator/SimulinkSimulatorView';
import CameraIQALab from './components/iqa/CameraIQALab';
import ClinicalGuidelinesView from './components/guidelines/ClinicalGuidelinesView';
import KaggleModelStudio from './components/kaggle/KaggleModelStudio';

import PatientRegistrationModal from './components/modals/PatientRegistrationModal';
import ImageUploadModal from './components/modals/ImageUploadModal';
import ClinicalReportModal from './components/modals/ClinicalReportModal';
import HospitalAuthModal from './components/auth/HospitalAuthModal';

import { apiClient } from './api/client';

export default function App() {
  const [activeTab, setActiveTab] = useState('triage');
  const [centers, setCenters] = useState([]);
  const [selectedCenter, setSelectedCenter] = useState(null);
  const [screenings, setScreenings] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [activeSessionDetail, setActiveSessionDetail] = useState(null);
  const [analyticsStats, setAnalyticsStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSeeding, setIsSeeding] = useState(false);

  // Hospital Authentication State
  const [hospital, setHospital] = useState(null);
  const [authToken, setAuthToken] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Modals state
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadSessionId, setUploadSessionId] = useState(null);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [reportSession, setReportSession] = useState(null);

  // Load initial data and verify hospital session
  const loadInitialData = async () => {
    setIsLoading(true);
    try {
      const savedToken = localStorage.getItem('mindhue_token');
      const savedHosp = localStorage.getItem('mindhue_hospital');

      if (savedToken && savedHosp) {
        setAuthToken(savedToken);
        try {
          setHospital(JSON.parse(savedHosp));
        } catch (e) {
          console.error(e);
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

      setCenters(centersData);
      if (centersData.length > 0) {
        setSelectedCenter(centersData[0]);
      }

      setScreenings(screeningsData);
      if (screeningsData.length > 0) {
        setActiveSessionId(screeningsData[0].id);
      }

      setAnalyticsStats(statsData);
    } catch (err) {
      console.error('Error loading initial data:', err);
    } finally {
      setIsLoading(false);
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
        .catch(err => console.error(err));
    }
  }, [activeSessionId]);

  // Handlers for Hospital Auth
  const handleLoginSuccess = (hospData, token) => {
    setHospital(hospData);
    setAuthToken(token);
    localStorage.setItem('mindhue_token', token);
    localStorage.setItem('mindhue_hospital', JSON.stringify(hospData));
    loadInitialData();
  };

  const handleLogoutHospital = () => {
    setHospital(null);
    setAuthToken(null);
    localStorage.removeItem('mindhue_token');
    localStorage.removeItem('mindhue_hospital');
  };

  // Handlers for screening workflow
  const handleSelectSession = (sessionId) => {
    setActiveSessionId(sessionId);
    setActiveTab('review');
  };

  const handleOpenUploadModal = (sessionId) => {
    setUploadSessionId(sessionId);
    setIsUploadModalOpen(true);
  };

  const handleViewReport = async (sessionId) => {
    try {
      const detail = await apiClient.getScreeningDetail(sessionId);
      setReportSession(detail);
      setIsReportModalOpen(true);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreatePatient = async (patientData) => {
    try {
      const newPatient = await apiClient.createPatient({
        ...patientData,
        hospital_account: hospital?.id || null
      });
      const newSession = await apiClient.createScreeningSession({
        patient: newPatient.id,
        session_code: `SESS-${newPatient.mrn}`,
        district_center: newPatient.district_center,
        hospital_account: hospital?.id || null
      });

      const updatedScreenings = await apiClient.getScreenings();
      setScreenings(updatedScreenings);
      handleOpenUploadModal(newSession.id);
    } catch (err) {
      console.error('Error creating patient:', err);
    }
  };

  const handleUploadSuccess = async () => {
    const [updatedScreenings, updatedStats] = await Promise.all([
      apiClient.getScreenings(),
      apiClient.getAnalyticsOverview()
    ]);
    setScreenings(updatedScreenings);
    setAnalyticsStats(updatedStats);

    if (uploadSessionId) {
      const detail = await apiClient.getScreeningDetail(uploadSessionId);
      setActiveSessionDetail(detail);
      setActiveSessionId(uploadSessionId);
      setActiveTab('review');
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
      console.error('Error seeding benchmark:', err);
    } finally {
      setIsSeeding(false);
    }
  };

  const pendingCount = screenings.filter(s => s.status === 'AI_GRADED' || s.status === 'PENDING_AI').length;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-[#005eb8] selection:text-white">
      
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
        
        {/* Navigation Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          pendingReviewCount={pendingCount}
          hospital={hospital}
          onOpenAuthModal={() => setIsAuthModalOpen(true)}
        />

        {/* Tab Content Area */}
        <main className="flex-1 p-4 lg:p-6 overflow-y-auto max-h-[calc(100vh-95px)] bg-slate-50">
          {activeTab === 'triage' && (
            <PatientTriageView
              patients={[]}
              screenings={screenings}
              onSelectSession={handleSelectSession}
              onOpenRegisterModal={() => setIsRegisterModalOpen(true)}
              onOpenUploadModal={handleOpenUploadModal}
              onViewReport={handleViewReport}
            />
          )}

          {activeTab === 'review' && (
            <FastReviewStudio
              session={activeSessionDetail || screenings[0]}
              onBack={() => setActiveTab('triage')}
              onValidate={handleValidateSession}
              onViewReport={handleViewReport}
            />
          )}

          {activeTab === 'canvas' && (
            <RetinalInspector
              session={activeSessionDetail || screenings[0]}
            />
          )}

          {activeTab === 'kaggle' && (
            <KaggleModelStudio />
          )}

          {activeTab === 'analytics' && (
            <DistrictEpidemiologyDashboard
              stats={analyticsStats}
              centers={centers}
            />
          )}

          {activeTab === 'simulator' && (
            <SimulinkSimulatorView
              onRunSimulation={apiClient.runSimulation}
            />
          )}

          {activeTab === 'iqa-lab' && (
            <CameraIQALab />
          )}

          {activeTab === 'guidelines' && (
            <ClinicalGuidelinesView />
          )}
        </main>

      </div>

      {/* Modals */}
      <HospitalAuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onLoginSuccess={handleLoginSuccess}
      />

      <PatientRegistrationModal
        isOpen={isRegisterModalOpen}
        onClose={() => setIsRegisterModalOpen(false)}
        onSubmit={handleCreatePatient}
        centers={centers}
        defaultCenterId={selectedCenter?.id}
      />

      <ImageUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        sessionId={uploadSessionId}
        onUploadSuccess={handleUploadSuccess}
      />

      <ClinicalReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        session={reportSession}
      />

    </div>
  );
}
