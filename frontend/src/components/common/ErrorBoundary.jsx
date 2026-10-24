import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('MindHue Tele-Retina Error Boundary caught an anomaly:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <div className="bg-white border border-red-200 rounded-2xl p-8 max-w-lg shadow-xl text-center">
            <div className="w-14 h-14 bg-red-50 text-red-600 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-red-100">
              <AlertTriangle className="w-7 h-7" />
            </div>
            <h2 className="text-xl font-extrabold text-slate-900 mb-2">
              Clinical View Rendering Anomaly
            </h2>
            <p className="text-xs text-slate-600 mb-6 leading-relaxed">
              A temporary display error occurred in the active workstation module. Diagnostic data and patient records remain safe in the database.
            </p>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-left mb-6 overflow-x-auto text-[11px] font-mono text-red-700">
              {this.state.error?.message || 'Unknown clinical rendering exception'}
            </div>
            <button
              onClick={this.handleReset}
              className="px-5 py-2.5 bg-[#005eb8] hover:bg-[#003087] text-white text-xs font-bold rounded-xl transition-all shadow-md cursor-pointer inline-flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Reload Workstation</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
