import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import EvidenceQueue from './pages/EvidenceQueue'
import EvidenceDetails from './pages/EvidenceDetails'
import ReviewPage from './pages/ReviewPage'
import AuditLogs from './pages/AuditLogs'
import Reports from './pages/Reports'
import UploadEvidence from './pages/UploadEvidence'
import BulkUploadEvidence from './pages/BulkUploadEvidence'
import OperationalEvaluationDashboard from './pages/OperationalEvaluationDashboard'
import ThresholdCalibration from './pages/ThresholdCalibration'
import ModelPerformanceDashboard from './pages/ModelPerformanceDashboard'
import ModelComparison from './pages/ModelComparison'
import TrainingPerformance from './pages/TrainingPerformance'
import ErrorAnalysis from './pages/ErrorAnalysis'
import Reproducibility from './pages/Reproducibility'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/dashboard" element={<ProtectedRoute><Navbar /><Dashboard /></ProtectedRoute>} />
      <Route path="/evidence" element={<ProtectedRoute><Navbar /><EvidenceQueue /></ProtectedRoute>} />
      <Route path="/evidence/upload" element={<ProtectedRoute><Navbar /><UploadEvidence /></ProtectedRoute>} />
      <Route path="/evidence/bulk-upload" element={<ProtectedRoute><Navbar /><BulkUploadEvidence /></ProtectedRoute>} />
      <Route path="/evidence/:id" element={<ProtectedRoute><Navbar /><EvidenceDetails /></ProtectedRoute>} />
      <Route path="/review/:id" element={<ProtectedRoute><Navbar /><ReviewPage /></ProtectedRoute>} />
      <Route path="/audit/:id" element={<ProtectedRoute><Navbar /><AuditLogs /></ProtectedRoute>} />
      <Route path="/reports" element={<ProtectedRoute><Navbar /><Reports /></ProtectedRoute>} />
      <Route path="/operational-evaluation" element={<ProtectedRoute><Navbar /><OperationalEvaluationDashboard /></ProtectedRoute>} />
      <Route path="/threshold-calibration" element={<ProtectedRoute><Navbar /><ThresholdCalibration /></ProtectedRoute>} />
      <Route path="/model-performance" element={<ProtectedRoute><Navbar /><ModelPerformanceDashboard /></ProtectedRoute>} />
      <Route path="/model-comparison" element={<ProtectedRoute><Navbar /><ModelComparison /></ProtectedRoute>} />
      <Route path="/training-performance" element={<ProtectedRoute><Navbar /><TrainingPerformance /></ProtectedRoute>} />
      <Route path="/error-analysis" element={<ProtectedRoute><Navbar /><ErrorAnalysis /></ProtectedRoute>} />
      <Route path="/reproducibility" element={<ProtectedRoute><Navbar /><Reproducibility /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
