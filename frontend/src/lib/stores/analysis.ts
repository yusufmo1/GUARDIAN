import { writable, derived } from 'svelte/store';
import type { AnalysisResult, AnalysisState, ComplianceFinding } from '$lib/types';
import { calculateComplianceScore } from '$lib/utils';

const defaultAnalysisState: AnalysisState = {
  results: [],
  current: null,
  processing: false,
  currentUserId: null
};

function createAnalysisStore() {
  const { subscribe, set, update } = writable<AnalysisState>(defaultAnalysisState);

  return {
    subscribe,
    
    // Analysis management
    addResult: (result: AnalysisResult) =>
      update(state => ({
        ...state,
        results: [...state.results, result]
      })),
    
    updateResult: (id: string, updates: Partial<AnalysisResult>) =>
      update(state => ({
        ...state,
        results: state.results.map(result =>
          result.id === id ? { ...result, ...updates } : result
        ),
        current: state.current?.id === id 
          ? { ...state.current, ...updates } 
          : state.current
      })),
    
    removeResult: (id: string) =>
      update(state => ({
        ...state,
        results: state.results.filter(result => result.id !== id),
        current: state.current?.id === id ? null : state.current
      })),
    
    setCurrent: (result: AnalysisResult | null) =>
      update(state => ({ ...state, current: result })),
    
    setProcessing: (processing: boolean) =>
      update(state => ({ ...state, processing })),
    
    // Finding management
    addFinding: (analysisId: string, finding: ComplianceFinding) =>
      update(state => ({
        ...state,
        results: state.results.map(result =>
          result.id === analysisId
            ? { 
                ...result, 
                findings: [...result.findings, finding],
                complianceScore: calculateComplianceScore([...result.findings, finding])
              }
            : result
        ),
        current: state.current?.id === analysisId
          ? {
              ...state.current,
              findings: [...state.current.findings, finding],
              complianceScore: calculateComplianceScore([...state.current.findings, finding])
            }
          : state.current
      })),
    
    updateFinding: (analysisId: string, findingId: string, updates: Partial<ComplianceFinding>) =>
      update(state => ({
        ...state,
        results: state.results.map(result =>
          result.id === analysisId
            ? {
                ...result,
                findings: result.findings.map(finding =>
                  finding.id === findingId ? { ...finding, ...updates } : finding
                ),
                complianceScore: calculateComplianceScore(
                  result.findings.map(finding =>
                    finding.id === findingId ? { ...finding, ...updates } : finding
                  )
                )
              }
            : result
        ),
        current: state.current?.id === analysisId
          ? {
              ...state.current,
              findings: state.current.findings.map(finding =>
                finding.id === findingId ? { ...finding, ...updates } : finding
              ),
              complianceScore: calculateComplianceScore(
                state.current.findings.map(finding =>
                  finding.id === findingId ? { ...finding, ...updates } : finding
                )
              )
            }
          : state.current
      })),
    
    removeFinding: (analysisId: string, findingId: string) =>
      update(state => ({
        ...state,
        results: state.results.map(result =>
          result.id === analysisId
            ? {
                ...result,
                findings: result.findings.filter(finding => finding.id !== findingId),
                complianceScore: calculateComplianceScore(
                  result.findings.filter(finding => finding.id !== findingId)
                )
              }
            : result
        ),
        current: state.current?.id === analysisId
          ? {
              ...state.current,
              findings: state.current.findings.filter(finding => finding.id !== findingId),
              complianceScore: calculateComplianceScore(
                state.current.findings.filter(finding => finding.id !== findingId)
              )
            }
          : state.current
      })),
    
    // User context management
    setCurrentUser: (userId: string | null) =>
      update(state => {
        // If user changed, clear all data
        if (state.currentUserId !== userId) {
          return {
            ...defaultAnalysisState,
            currentUserId: userId
          };
        }
        return { ...state, currentUserId: userId };
      }),
    
    // Bulk operations
    clearAll: () => set(defaultAnalysisState),
    
    clearCompleted: () =>
      update(state => ({
        ...state,
        results: state.results.filter(result => result.status !== 'completed')
      }))
  };
}

export const analysisStore = createAnalysisStore();

// Derived stores
export const analysisCount = derived(
  analysisStore,
  $analysisStore => $analysisStore.results.length
);

export const processingAnalysis = derived(
  analysisStore,
  $analysisStore => $analysisStore.results.filter(result => 
    result.status === 'processing' || result.status === 'pending'
  )
);

export const completedAnalysis = derived(
  analysisStore,
  $analysisStore => $analysisStore.results.filter(result => result.status === 'completed')
);

export const errorAnalysis = derived(
  analysisStore,
  $analysisStore => $analysisStore.results.filter(result => result.status === 'error')
);

export const averageComplianceScore = derived(
  completedAnalysis,
  $completedAnalysis => {
    if ($completedAnalysis.length === 0) return 0;
    const total = $completedAnalysis.reduce((sum, result) => sum + result.complianceScore, 0);
    return Math.round(total / $completedAnalysis.length);
  }
);

export const criticalFindings = derived(
  analysisStore,
  $analysisStore => {
    if (!$analysisStore.current) return [];
    return $analysisStore.current.findings.filter(finding => finding.severity === 'critical');
  }
);

export const nonCompliantFindings = derived(
  analysisStore,
  $analysisStore => {
    if (!$analysisStore.current) return [];
    return $analysisStore.current.findings.filter(finding => finding.status === 'non-compliant');
  }
);