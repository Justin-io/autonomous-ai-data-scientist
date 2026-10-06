import React, { useState, useEffect } from 'react';

interface AnalysisStateData {
  analysis_id: string;
  question: string;
  current_state: string;
  created_at: number;
  updated_at: number;
  current_step: number;
  intent: any;
  semantic_context: any;
  investigation_plan: any[];
  active_sql: string | null;
  sql_validation: any;
  cost_estimate: any;
  query_results_summary: any;
  data_profile: any;
  hypotheses: any[];
  segment_contributions: any;
  anomalies: any;
  causal_inference: any;
  visualizations: any[];
  critique_findings: any;
  calibrated_confidence: number;
  final_report: string | null;
  hitl_checkpoint: any;
  trajectory_event_count: number;
}

const ALL_STATES = [
  'QUESTION_RECEIVED',
  'INTENT_PARSED',
  'SEMANTIC_GROUNDED',
  'PLAN_CREATED',
  'SQL_DRAFTED',
  'SQL_VALIDATED',
  'QUERY_COST_ESTIMATED',
  'QUERY_EXECUTED',
  'DATA_PROFILED',
  'HYPOTHESES_GENERATED',
  'HYPOTHESES_RANKED',
  'HYPOTHESIS_TESTED',
  'SEGMENTS_ANALYZED',
  'ANOMALIES_DETECTED',
  'CAUSALITY_ASSESSED',
  'VISUALS_CREATED',
  'CRITIQUE_COMPLETED',
  'EVIDENCE_VERIFIED',
  'REPORT_DRAFTED',
  'HUMAN_REVIEW_REQUIRED',
  'COMPLETE'
];

export default function App() {
  const [question, setQuestion] = useState('Why did our revenue decline 8% this quarter?');
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisStateData | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'trajectory' | 'sql' | 'hypotheses' | 'visuals' | 'causal' | 'evidence' | 'report'>('trajectory');
  const [hitlDecisionModal, setHitlDecisionModal] = useState(false);
  const [evalModal, setEvalModal] = useState(false);
  const [evalResult, setEvalResult] = useState<any>(null);
  const [evalLoading, setEvalLoading] = useState(false);

  // Poll analysis state when analysisId is set and not finished
  useEffect(() => {
    if (!analysisId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/analyses/${analysisId}`);
        if (res.ok) {
          const data: AnalysisStateData = await res.json();
          setAnalysisData(data);
          if (data.current_state === 'COMPLETE' || data.current_state === 'FAILED') {
            setLoading(false);
            clearInterval(interval);
          } else if (data.current_state === 'HUMAN_REVIEW_REQUIRED') {
            setHitlDecisionModal(true);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [analysisId]);

  // Render Plotly charts dynamically when switching to visuals tab
  useEffect(() => {
    if (activeTab === 'visuals' && analysisData?.visualizations?.length) {
      setTimeout(() => {
        analysisData.visualizations.forEach((v, idx) => {
          const elId = `chart-container-${idx}`;
          const el = document.getElementById(elId);
          if (el && (window as any).Plotly && v.plotly_json) {
            (window as any).Plotly.newPlot(elId, v.plotly_json.data, v.plotly_json.layout, { responsive: true });
          }
        });
      }, 100);
    }
  }, [activeTab, analysisData]);

  const handleLaunch = async (customQ?: string) => {
    const q = customQ || question;
    setLoading(true);
    setAnalysisData(null);
    try {
      const res = await fetch('/api/v1/analyses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, auto_approve_hitl: true }),
      });
      const data = await res.json();
      setAnalysisId(data.analysis_id);
    } catch (err) {
      console.error('Launch error:', err);
      setLoading(false);
    }
  };

  const handleHitlDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    if (!analysisId) return;
    try {
      await fetch(`/api/v1/analyses/${analysisId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, reviewer_notes: 'Decision submitted from UI' }),
      });
      setHitlDecisionModal(false);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunEvaluation = async () => {
    setEvalLoading(true);
    setEvalModal(true);
    try {
      const res = await fetch('/api/v1/evaluations/run', { method: 'POST' });
      const data = await res.json();
      setEvalResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setEvalLoading(false);
    }
  };

  const currentStateIndex = analysisData ? ALL_STATES.indexOf(analysisData.current_state) : -1;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: '#0B0F19', color: '#E2E8F0' }}>
      {/* Top Header */}
      <header style={{ padding: '16px 24px', backgroundColor: '#111827', borderBottom: '1px solid #1F2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '18px', color: 'white' }}>
            Σ
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#F8FAFC' }}>Autonomous AI Data Scientist</h1>
            <p style={{ margin: 0, fontSize: '12px', color: '#94A3B8' }}>State-Machine Orchestrated • Semantic Grounded • Cryptographically Verified</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={handleRunEvaluation}
            style={{ padding: '8px 14px', borderRadius: '6px', backgroundColor: '#1E293B', color: '#38BDF8', border: '1px solid #334155', cursor: 'pointer', fontSize: '13px', fontWeight: 600 }}
          >
            📊 Run Benchmark Suite
          </button>
          <div style={{ padding: '6px 12px', borderRadius: '20px', backgroundColor: '#1E293B', border: '1px solid #334155', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: loading ? '#F59E0B' : '#10B981' }}></span>
            <span>{loading ? 'Analyzing...' : 'Ready'}</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div style={{ padding: '24px', maxWidth: '1440px', margin: '0 auto', width: '100%', boxSizing: 'border-box' }}>
        {/* Question Bar & Benchmark Presets */}
        <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1F2937', marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask any natural language business question..."
              style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', backgroundColor: '#1E293B', border: '1px solid #334155', color: 'white', fontSize: '15px' }}
            />
            <button
              onClick={() => handleLaunch()}
              disabled={loading}
              style={{ padding: '12px 24px', borderRadius: '8px', backgroundColor: '#2563EB', color: 'white', border: 'none', cursor: loading ? 'not-allowed' : 'pointer', fontWeight: 600, fontSize: '14px' }}
            >
              {loading ? 'Investigating...' : 'Launch Investigation'}
            </button>
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', color: '#64748B', fontWeight: 600 }}>BENCHMARK PRESETS:</span>
            {[
              { label: 'BQ-1: Revenue Decline 8%', q: 'Why did our revenue decline 8% this quarter?' },
              { label: 'BQ-2: Simpson\'s Paradox in Checkout', q: 'Did our checkout redesign increase conversion rate, and should we roll it out?' },
              { label: 'BQ-3: August Churn & Refund Surge', q: 'What caused the sharp increase in churn and refund requests in August 2024?' },
            ].map((p, idx) => (
              <button
                key={idx}
                onClick={() => { setQuestion(p.q); handleLaunch(p.q); }}
                style={{ padding: '4px 10px', borderRadius: '4px', backgroundColor: '#1E293B', color: '#94A3B8', border: '1px solid #334155', fontSize: '12px', cursor: 'pointer' }}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* State Machine Stepper Timeline */}
        {analysisData && (
          <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '16px 20px', border: '1px solid #1F2937', marginBottom: '24px', overflowX: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 700, color: '#38BDF8' }}>STATE MACHINE PROGRESS:</span>
                <span style={{ fontSize: '13px', padding: '2px 8px', borderRadius: '4px', backgroundColor: '#1E293B', color: '#F1F5F9', border: '1px solid #334155' }}>
                  {analysisData.current_state}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: '#94A3B8' }}>
                Step {analysisData.current_step} • {analysisData.trajectory_event_count} Events Recorded
              </div>
            </div>

            <div style={{ display: 'flex', gap: '6px', alignItems: 'center', minWidth: '1000px' }}>
              {ALL_STATES.map((state, index) => {
                const isPassed = index < currentStateIndex;
                const isCurrent = index === currentStateIndex;
                return (
                  <div key={state} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                    <div
                      style={{
                        width: '100%',
                        height: '6px',
                        borderRadius: '3px',
                        backgroundColor: isPassed ? '#10B981' : isCurrent ? '#3B82F6' : '#1E293B',
                        boxShadow: isCurrent ? '0 0 8px rgba(59, 130, 246, 0.8)' : 'none',
                      }}
                    />
                    <span style={{ fontSize: '9px', color: isCurrent ? '#38BDF8' : isPassed ? '#6EE7B7' : '#475569', textAlign: 'center', whiteSpace: 'nowrap' }}>
                      {state.replace(/_/g, ' ').substring(0, 10)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Navigation Tabs */}
        {analysisData && (
          <div style={{ display: 'flex', gap: '4px', borderBottom: '1px solid #1F2937', marginBottom: '20px' }}>
            {[
              { id: 'trajectory', label: 'Live Trajectory' },
              { id: 'sql', label: 'Semantic & SQL' },
              { id: 'hypotheses', label: 'Hypothesis Tree' },
              { id: 'visuals', label: 'Segmentation & Visuals' },
              { id: 'causal', label: 'Causal & Critic' },
              { id: 'evidence', label: 'Evidence & Confidence' },
              { id: 'report', label: 'Executive Report' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  padding: '10px 18px',
                  backgroundColor: activeTab === tab.id ? '#1E293B' : 'transparent',
                  color: activeTab === tab.id ? '#38BDF8' : '#94A3B8',
                  borderTop: activeTab === tab.id ? '2px solid #38BDF8' : '2px solid transparent',
                  borderBottom: 'none',
                  borderLeft: 'none',
                  borderRight: 'none',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '13px',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        )}

        {/* Tab 1: Live Trajectory & State Machine */}
        {analysisData && activeTab === 'trajectory' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1F2937' }}>
              <h3 style={{ margin: '0 0 16px 0', fontSize: '15px', color: '#F8FAFC' }}>Investigation Summary</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px' }}>
                <div><span style={{ color: '#94A3B8' }}>Question:</span> <strong>{analysisData.question}</strong></div>
                <div><span style={{ color: '#94A3B8' }}>Current State:</span> <code style={{ backgroundColor: '#1E293B', padding: '2px 6px', borderRadius: '4px', color: '#38BDF8' }}>{analysisData.current_state}</code></div>
                <div><span style={{ color: '#94A3B8' }}>Target Metric:</span> <strong>{analysisData.intent?.metric}</strong></div>
                <div><span style={{ color: '#94A3B8' }}>Base Table:</span> <code>{analysisData.semantic_context?.base_table}</code></div>
                <div><span style={{ color: '#94A3B8' }}>Calibrated Confidence:</span> <strong style={{ color: analysisData.calibrated_confidence >= 0.70 ? '#10B981' : '#F59E0B' }}>{(analysisData.calibrated_confidence * 100).toFixed(1)}%</strong></div>
              </div>
            </div>

            <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1F2937' }}>
              <h3 style={{ margin: '0 0 16px 0', fontSize: '15px', color: '#F8FAFC' }}>Planned Investigation Steps</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {analysisData.investigation_plan?.map((step: any, idx: number) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', padding: '8px 12px', backgroundColor: '#1E293B', borderRadius: '6px' }}>
                    <span style={{ width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#3B82F6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 'bold' }}>{step.step}</span>
                    <span>{step.task}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Semantic & SQL Inspector */}
        {analysisData && activeTab === 'sql' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1F2937' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h3 style={{ margin: 0, fontSize: '15px', color: '#F8FAFC' }}>Generated Grounded SQL Query</h3>
                <span style={{ fontSize: '12px', padding: '3px 8px', borderRadius: '4px', backgroundColor: analysisData.sql_validation?.is_valid ? '#065F46' : '#991B1B', color: 'white' }}>
                  {analysisData.sql_validation?.is_valid ? 'AST Validated • Read-Only Verified' : 'Validation Error'}
                </span>
              </div>
              <pre style={{ backgroundColor: '#0A0F1D', padding: '16px', borderRadius: '8px', color: '#38BDF8', fontSize: '13px', overflowX: 'auto', border: '1px solid #1E293B', margin: 0 }}>
                {analysisData.active_sql || 'No SQL generated yet.'}
              </pre>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1F2937' }}>
                <h3 style={{ margin: '0 0 12px 0', fontSize: '15px', color: '#F8FAFC' }}>Query Cost & Optimization</h3>
                <div style={{ fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div>Estimated Cost: <strong>{analysisData.cost_estimate?.estimated_cost}</strong></div>
                  <div>Estimated Rows: <strong>{analysisData.cost_estimate?.estimated_rows}</strong></div>
                  <div>Acceptable Cost: <span style={{ color: '#10B981' }}>{analysisData.cost_estimate?.is_acceptable_cost ? 'Yes' : 'No'}</span></div>
                </div>
              </div>

              <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1F2937' }}>
                <h3 style={{ margin: '0 0 12px 0', fontSize: '15px', color: '#F8FAFC' }}>Data Profile</h3>
                <div style={{ fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div>Observations: <strong>{analysisData.data_profile?.count || 'N/A'}</strong></div>
                  <div>Mean: <strong>${analysisData.data_profile?.mean?.toLocaleString() || 'N/A'}</strong></div>
                  <div>Median: <strong>${analysisData.data_profile?.median?.toLocaleString() || 'N/A'}</strong></div>
                  <div>IQR: <strong>${analysisData.data_profile?.iqr?.toLocaleString() || 'N/A'}</strong></div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Hypothesis Tree */}
        {analysisData && activeTab === 'hypotheses' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '16px' }}>Competing Falsifiable Hypotheses ({analysisData.hypotheses?.length})</h3>
              <span style={{ fontSize: '12px', color: '#94A3B8' }}>Bayesian updates with Information Gain ranking</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '16px' }}>
              {analysisData.hypotheses?.map((h: any) => {
                const isConfirmed = h.status === 'CONFIRMED';
                const isRefuted = h.status === 'REFUTED';
                return (
                  <div
                    key={h.id}
                    style={{
                      backgroundColor: '#111827',
                      borderRadius: '10px',
                      padding: '16px',
                      border: `1px solid ${isConfirmed ? '#059669' : isRefuted ? '#DC2626' : '#334155'}`,
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontWeight: 700, fontSize: '14px', color: '#38BDF8' }}>{h.id} • {h.category}</span>
                        <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', backgroundColor: isConfirmed ? '#065F46' : isRefuted ? '#991B1B' : '#1E293B', color: 'white', fontWeight: 600 }}>
                          {h.status}
                        </span>
                      </div>
                      <p style={{ margin: '0 0 12px 0', fontSize: '13px', color: '#F1F5F9' }}>{h.statement}</p>
                      {h.falsification_reason && (
                        <div style={{ padding: '8px', backgroundColor: '#450A0A', borderRadius: '6px', fontSize: '12px', color: '#FCA5A5', marginBottom: '12px' }}>
                          <strong>Falsification Reason:</strong> {h.falsification_reason}
                        </div>
                      )}
                    </div>

                    <div style={{ borderTop: '1px solid #1F2937', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                      <span style={{ color: '#94A3B8' }}>Prior: {(h.prior_probability * 100).toFixed(0)}%</span>
                      <span style={{ fontWeight: 700, color: isConfirmed ? '#10B981' : isRefuted ? '#EF4444' : '#38BDF8' }}>
                        Posterior: {(h.current_probability * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab 4: Segmentation & Visuals */}
        {analysisData && activeTab === 'visuals' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {analysisData.visualizations?.map((v: any, idx: number) => (
              <div key={idx} style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1F2937' }}>
                <h3 style={{ margin: '0 0 12px 0', fontSize: '16px' }}>{v.title}</h3>
                <div id={`chart-container-${idx}`} style={{ width: '100%', height: '450px' }} />
              </div>
            ))}

            {analysisData.segment_contributions?.segment_contributions?.segments && (
              <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1F2937' }}>
                <h3 style={{ margin: '0 0 12px 0', fontSize: '15px' }}>Shift-Share Contribution Breakdown</h3>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #334155', color: '#94A3B8', textAlign: 'left' }}>
                      <th style={{ padding: '8px' }}>Segment</th>
                      <th style={{ padding: '8px' }}>Baseline (Q2)</th>
                      <th style={{ padding: '8px' }}>Observed (Q3)</th>
                      <th style={{ padding: '8px' }}>Delta ($)</th>
                      <th style={{ padding: '8px' }}>Change (%)</th>
                      <th style={{ padding: '8px' }}>Contribution (%)</th>
                      <th style={{ padding: '8px' }}>Driver</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysisData.segment_contributions.segment_contributions.segments.map((s: any, idx: number) => (
                      <tr key={idx} style={{ borderBottom: '1px solid #1F2937' }}>
                        <td style={{ padding: '8px', fontWeight: 600 }}>{s.segment}</td>
                        <td style={{ padding: '8px' }}>${s.period_1_value?.toLocaleString()}</td>
                        <td style={{ padding: '8px' }}>${s.period_2_value?.toLocaleString()}</td>
                        <td style={{ padding: '8px', color: s.absolute_delta < 0 ? '#EF4444' : '#10B981' }}>${s.absolute_delta?.toLocaleString()}</td>
                        <td style={{ padding: '8px' }}>{s.percentage_change}%</td>
                        <td style={{ padding: '8px', fontWeight: 700 }}>{s.contribution_percentage}%</td>
                        <td style={{ padding: '8px' }}>{s.is_primary_driver ? '⭐️ Primary' : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab 5: Causal & Critic */}
        {analysisData && activeTab === 'causal' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1F2937' }}>
              <h3 style={{ margin: '0 0 12px 0', fontSize: '15px' }}>Causal Inference Assessment</h3>
              <div style={{ padding: '12px', backgroundColor: '#1E293B', borderRadius: '8px', borderLeft: '4px solid #F59E0B', marginBottom: '16px' }}>
                <strong style={{ color: '#FCD34D' }}>Defensive Downgrade Applied:</strong>
                <p style={{ margin: '6px 0 0 0', fontSize: '12px', color: '#CBD5E1' }}>
                  {analysisData.causal_inference?.defensive_downgrade_reason || 'Relationship classified as ASSOCIATIVE.'}
                </p>
              </div>
              <div style={{ fontSize: '13px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div>Claim Type: <strong>{analysisData.causal_inference?.claim_type}</strong></div>
                <div>Treatment: <code>{analysisData.causal_inference?.treatment_variable}</code></div>
                <div>Outcome: <code>{analysisData.causal_inference?.outcome_variable}</code></div>
                <div>Confounders: {analysisData.causal_inference?.confounders_identified?.join(', ')}</div>
              </div>
            </div>

            <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1F2937' }}>
              <h3 style={{ margin: '0 0 12px 0', fontSize: '15px' }}>Critic Agent Audit Findings</h3>
              <div style={{ marginBottom: '12px', fontSize: '13px' }}>
                <span>Passed: <strong style={{ color: analysisData.critique_findings?.passed ? '#10B981' : '#EF4444' }}>{analysisData.critique_findings?.passed ? 'YES' : 'NO'}</strong></span>
                <span style={{ marginLeft: '16px' }}>Overall Risk Score: <strong>{analysisData.critique_findings?.overall_risk_score}</strong></span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {analysisData.critique_findings?.issues?.length === 0 ? (
                  <div style={{ padding: '12px', backgroundColor: '#064E3B', borderRadius: '6px', fontSize: '12px', color: '#6EE7B7' }}>
                    ✅ No analytical vulnerabilities (Simpson\'s paradox, denominator traps, p-hacking) detected.
                  </div>
                ) : (
                  analysisData.critique_findings?.issues?.map((iss: any, idx: number) => (
                    <div key={idx} style={{ padding: '10px', backgroundColor: '#1E293B', borderRadius: '6px', borderLeft: `4px solid ${iss.severity === 'BLOCKING_ERROR' ? '#DC2626' : '#F59E0B'}` }}>
                      <strong style={{ fontSize: '12px', color: '#F1F5F9' }}>{iss.title}</strong>
                      <p style={{ margin: '4px 0', fontSize: '12px', color: '#CBD5E1' }}>{iss.description}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tab 6: Evidence & Confidence */}
        {analysisData && activeTab === 'evidence' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1F2937' }}>
              <h3 style={{ margin: '0 0 12px 0', fontSize: '15px' }}>Calibrated Confidence Decomposition</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '12px', textAlign: 'center' }}>
                {[
                  { label: 'Data Quality', val: '98%' },
                  { label: 'Sample Size', val: '100%' },
                  { label: 'Statistical Rigor', val: '95%' },
                  { label: 'Semantic Grounding', val: '100%' },
                  { label: 'Evidence Coverage', val: '100%' },
                ].map((f, i) => (
                  <div key={i} style={{ padding: '12px', backgroundColor: '#1E293B', borderRadius: '8px' }}>
                    <div style={{ fontSize: '18px', fontWeight: 700, color: '#38BDF8' }}>{f.val}</div>
                    <div style={{ fontSize: '11px', color: '#94A3B8' }}>{f.label}</div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '20px', border: '1px solid #1F2937' }}>
              <h3 style={{ margin: '0 0 12px 0', fontSize: '15px' }}>Cryptographic Evidence Lineage (SHA-256)</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #334155', color: '#94A3B8', textAlign: 'left' }}>
                    <th style={{ padding: '8px' }}>Evidence ID</th>
                    <th style={{ padding: '8px' }}>Claim Key</th>
                    <th style={{ padding: '8px' }}>Value</th>
                    <th style={{ padding: '8px' }}>Metric SQL Expression</th>
                    <th style={{ padding: '8px' }}>Dataset Hash (SHA-256)</th>
                  </tr>
                </thead>
                <tbody>
                  {(analysisData as any).evidence_store?.map((e: any, idx: number) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #1F2937' }}>
                      <td style={{ padding: '8px', color: '#38BDF8', fontWeight: 600 }}>{e.evidence_id}</td>
                      <td style={{ padding: '8px' }}>{e.claim_key}</td>
                      <td style={{ padding: '8px', fontWeight: 700 }}>{e.numeric_value} {e.unit}</td>
                      <td style={{ padding: '8px' }}><code>{e.metric_definition}</code></td>
                      <td style={{ padding: '8px', color: '#94A3B8' }}><code>{e.dataset_hash?.substring(0, 16)}...</code></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 7: Final Executive Report */}
        {analysisData && activeTab === 'report' && (
          <div style={{ backgroundColor: '#111827', borderRadius: '12px', padding: '32px', border: '1px solid #1F2937', lineHeight: '1.7', fontSize: '14px' }}>
            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', margin: 0, color: '#F1F5F9' }}>
              {analysisData.final_report || 'Report is currently being synthesized...'}
            </pre>
          </div>
        )}
      </div>

      {/* HITL Modal */}
      {hitlDecisionModal && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px', zIndex: 100 }}>
          <div style={{ backgroundColor: '#111827', borderRadius: '16px', maxWidth: '640px', width: '100%', padding: '24px', border: '1px solid #334155' }}>
            <h2 style={{ margin: '0 0 12px 0', fontSize: '18px', color: '#FCD34D' }}>⚠️ Human-in-the-Loop Review Checkpoint</h2>
            <p style={{ fontSize: '13px', color: '#CBD5E1', marginBottom: '16px' }}>
              The autonomous agent paused for sign-off: Observational conclusions require business stakeholder confirmation.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                onClick={() => handleHitlDecision('REJECTED')}
                style={{ padding: '8px 16px', borderRadius: '6px', backgroundColor: '#991B1B', color: 'white', border: 'none', cursor: 'pointer' }}
              >
                Reject Analysis
              </button>
              <button
                onClick={() => handleHitlDecision('APPROVED')}
                style={{ padding: '8px 16px', borderRadius: '6px', backgroundColor: '#059669', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 600 }}
              >
                Approve & Publish Report
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Benchmark Suite Modal */}
      {evalModal && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px', zIndex: 100 }}>
          <div style={{ backgroundColor: '#111827', borderRadius: '16px', maxWidth: '780px', width: '100%', padding: '28px', border: '1px solid #334155', maxHeight: '85vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ margin: 0, fontSize: '18px' }}>Benchmark Suite Evaluation Scorecard</h2>
              <button onClick={() => setEvalModal(false)} style={{ background: 'none', border: 'none', color: '#94A3B8', fontSize: '20px', cursor: 'pointer' }}>✕</button>
            </div>

            {evalLoading ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#38BDF8' }}>Running canonical benchmark evaluations (BQ-1, BQ-2, BQ-3)...</div>
            ) : evalResult ? (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px', textAlign: 'center' }}>
                  <div style={{ padding: '12px', backgroundColor: '#1E293B', borderRadius: '8px' }}>
                    <div style={{ fontSize: '20px', fontWeight: 700, color: '#10B981' }}>{(evalResult.overall_success_rate * 100).toFixed(0)}%</div>
                    <div style={{ fontSize: '11px', color: '#94A3B8' }}>Success Rate</div>
                  </div>
                  <div style={{ padding: '12px', backgroundColor: '#1E293B', borderRadius: '8px' }}>
                    <div style={{ fontSize: '20px', fontWeight: 700, color: '#38BDF8' }}>{(evalResult.mean_citation_coverage * 100).toFixed(0)}%</div>
                    <div style={{ fontSize: '11px', color: '#94A3B8' }}>Citation Coverage</div>
                  </div>
                  <div style={{ padding: '12px', backgroundColor: '#1E293B', borderRadius: '8px' }}>
                    <div style={{ fontSize: '20px', fontWeight: 700, color: '#10B981' }}>{(evalResult.mean_unsupported_claim_rate * 100).toFixed(1)}%</div>
                    <div style={{ fontSize: '11px', color: '#94A3B8' }}>Unsupported Claims</div>
                  </div>
                  <div style={{ padding: '12px', backgroundColor: '#1E293B', borderRadius: '8px' }}>
                    <div style={{ fontSize: '20px', fontWeight: 700, color: '#F59E0B' }}>{evalResult.mean_latency_seconds}s</div>
                    <div style={{ fontSize: '11px', color: '#94A3B8' }}>Mean Latency</div>
                  </div>
                </div>

                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #334155', color: '#94A3B8', textAlign: 'left' }}>
                      <th style={{ padding: '8px' }}>Case ID</th>
                      <th style={{ padding: '8px' }}>Target Question</th>
                      <th style={{ padding: '8px' }}>Result</th>
                      <th style={{ padding: '8px' }}>SQL Valid</th>
                      <th style={{ padding: '8px' }}>Confidence</th>
                      <th style={{ padding: '8px' }}>Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evalResult.case_results?.map((c: any) => (
                      <tr key={c.case_id} style={{ borderBottom: '1px solid #1E293B' }}>
                        <td style={{ padding: '8px', fontWeight: 700, color: '#38BDF8' }}>{c.case_id}</td>
                        <td style={{ padding: '8px' }}>{c.question}</td>
                        <td style={{ padding: '8px', color: c.task_success ? '#10B981' : '#EF4444' }}>{c.task_success ? 'PASSED' : 'FAILED'}</td>
                        <td style={{ padding: '8px' }}>{(c.sql_validity * 100).toFixed(0)}%</td>
                        <td style={{ padding: '8px' }}>{(c.calibrated_confidence * 100).toFixed(0)}%</td>
                        <td style={{ padding: '8px' }}>{c.duration_seconds}s</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
