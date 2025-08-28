import type { AnalysisResult, ComplianceFinding, User } from '$lib/types';

// Create reactive analysis state using Svelte 5 runes
let results = $state<AnalysisResult[]>([]);
let current = $state<AnalysisResult | null>(null);
let processing = $state(false);
let currentUserId = $state<string | null>(null);

// Derived computations for analysis management (converted to getter functions)
export function analysisCount() { return results.length; }

export function processingAnalysis() {
  return results.filter(result => 
    result.status === 'processing' || result.status === 'pending'
  );
}

export function completedAnalysis() {
  return results.filter(result => result.status === 'completed');
}

export function errorAnalysis() {
  return results.filter(result => result.status === 'error');
}

export function averageComplianceScore() {
  const completed = completedAnalysis();
  if (completed.length === 0) return 0;
  const total = completed.reduce((sum, result) => sum + result.complianceScore, 0);
  return Math.round(total / completed.length);
}

export function criticalFindings() {
  if (!current) return [];
  return current.findings.filter(finding => finding.severity === 'critical');
}

export function nonCompliantFindings() {
  if (!current) return [];
  return current.findings.filter(finding => finding.status === 'non-compliant');
}

// Additional derived computations for enhanced UX
export function hasResults() { return results.length > 0; }
export function hasCurrentAnalysis() { return current !== null; }
export function isProcessing() { return processing; }
export function processingCount() { return processingAnalysis().length; }
export function completedCount() { return completedAnalysis().length; }
export function errorCount() { return errorAnalysis().length; }

// Advanced derived computations
export function currentAnalysisFindings() { return current?.findings || []; }
export function currentComplianceScore() { return current?.complianceScore || 0; }
export function currentAnalysisStatus() { return current?.status || null; }

export function findingsBySeverity() {
  if (!current) return { critical: [], major: [], minor: [], info: [] };
  
  return current.findings.reduce((acc, finding) => {
    acc[finding.severity].push(finding);
    return acc;
  }, { critical: [], major: [], minor: [], info: [] } as Record<string, ComplianceFinding[]>);
}

export function findingsByStatus() {
  if (!current) return { compliant: [], 'non-compliant': [], partial: [], 'needs-review': [] };
  
  return current.findings.reduce((acc, finding) => {
    acc[finding.status].push(finding);
    return acc;
  }, { 
    compliant: [], 
    'non-compliant': [], 
    partial: [], 
    'needs-review': [] 
  } as Record<string, ComplianceFinding[]>);
}

export function complianceStats() {
  if (!current) return { total: 0, compliant: 0, nonCompliant: 0, partial: 0, needsReview: 0 };
  
  const stats = {
    total: current.findings.length,
    compliant: 0,
    nonCompliant: 0,
    partial: 0,
    needsReview: 0
  };
  
  current.findings.forEach(finding => {
    switch (finding.status) {
      case 'compliant':
        stats.compliant++;
        break;
      case 'non-compliant':
        stats.nonCompliant++;
        break;
      case 'partial':
        stats.partial++;
        break;
      case 'needs-review':
        stats.needsReview++;
        break;
    }
  });
  
  return stats;
}

// Note: User isolation moved to component initialization
// Store-level effects are not allowed in Svelte 5

// Analysis store interface - maintains compatibility with existing code
export const analysisStore = {
  // Getters for reactive access
  get results(): AnalysisResult[] {
    return results;
  },
  
  get current(): AnalysisResult | null {
    return current;
  },
  
  get processing(): boolean {
    return processing;
  },
  
  get currentUserId(): string | null {
    return currentUserId;
  },
  
  // Analysis management
  addResult(result: Omit<AnalysisResult, 'id' | 'createdAt'>): string {
    const newResult: AnalysisResult = {
      ...result,
      id: `analysis_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      createdAt: new Date()
    };
    
    results = [...results, newResult];
    
    // Set as current if none is selected
    if (!current) {
      current = newResult;
    }
    
    console.log(`Analysis result added: ${newResult.id}`);
    return newResult.id;
  },
  
  updateResult(id: string, updates: Partial<AnalysisResult>): void {
    results = results.map(result =>
      result.id === id ? { ...result, ...updates } : result
    );
    
    // Update current if it matches
    if (current?.id === id) {
      current = { ...current, ...updates };
    }
  },
  
  removeResult(id: string): void {
    results = results.filter(result => result.id !== id);
    
    // Clear current if the removed result was current
    if (current?.id === id) {
      current = results.length > 0 ? results[0] : null;
    }
  },
  
  setCurrent(id: string | null): void {
    if (id === null) {
      current = null;
    } else {
      const result = results.find(r => r.id === id);
      current = result || null;
    }
  },
  
  setProcessing(isProcessing: boolean): void {
    processing = isProcessing;
  },
  
  // User context management
  setCurrentUser(userId: string | null): void {
    const previousUserId = currentUserId;
    
    // If user changed, clear all data
    if (previousUserId !== userId) {
      console.log(`Analysis: User changed from ${previousUserId} to ${userId}, clearing data`);
      
      results = [];
      current = null;
      processing = false;
    }
    
    currentUserId = userId;
  },
  
  // Bulk operations
  clearAll(): void {
    console.log('Analysis: Clearing all data');
    results = [];
    current = null;
    processing = false;
    currentUserId = null;
  },
  
  clearCompleted(): void {
    const completedIds = new Set(
      results.filter(r => r.status === 'completed').map(r => r.id)
    );
    
    results = results.filter(result => !completedIds.has(result.id));
    
    // Clear current if it was completed
    if (current && completedIds.has(current.id)) {
      current = results.length > 0 ? results[0] : null;
    }
  },
  
  // Statistics and analytics
  getAnalysisStats() {
    return {
      total: results.length,
      processing: processingAnalysis().length,
      completed: completedAnalysis().length,
      error: errorAnalysis().length,
      averageScore: averageComplianceScore()
    };
  },
  
  getResultById(id: string): AnalysisResult | undefined {
    return results.find(result => result.id === id);
  },
  
  getResultsByStatus(status: AnalysisResult['status']): AnalysisResult[] {
    return results.filter(result => result.status === status);
  },
  
  // Compliance score calculations
  updateComplianceScore(analysisId: string, findings: ComplianceFinding[]): void {
    const totalFindings = findings.length;
    if (totalFindings === 0) return;
    
    const compliantFindings = findings.filter(f => f.status === 'compliant').length;
    const partiallyCompliantFindings = findings.filter(f => f.status === 'partial').length;
    
    // Calculate weighted score: compliant = 100%, partial = 50%
    const score = Math.round(
      ((compliantFindings * 100) + (partiallyCompliantFindings * 50)) / totalFindings
    );
    
    this.updateResult(analysisId, { 
      complianceScore: score,
      findings: findings,
      completedAt: new Date()
    });
  },
  
  // Finding management
  addFinding(analysisId: string, finding: Omit<ComplianceFinding, 'id'>): string {
    const analysis = results.find(r => r.id === analysisId);
    if (!analysis) return '';
    
    const newFinding: ComplianceFinding = {
      ...finding,
      id: `finding_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };
    
    const updatedFindings = [...analysis.findings, newFinding];
    this.updateResult(analysisId, { findings: updatedFindings });
    
    // Recalculate compliance score
    this.updateComplianceScore(analysisId, updatedFindings);
    
    return newFinding.id;
  },
  
  updateFinding(analysisId: string, findingId: string, updates: Partial<ComplianceFinding>): void {
    const analysis = results.find(r => r.id === analysisId);
    if (!analysis) return;
    
    const updatedFindings = analysis.findings.map(finding =>
      finding.id === findingId ? { ...finding, ...updates } : finding
    );
    
    this.updateResult(analysisId, { findings: updatedFindings });
    
    // Recalculate compliance score
    this.updateComplianceScore(analysisId, updatedFindings);
  },
  
  removeFinding(analysisId: string, findingId: string): void {
    const analysis = results.find(r => r.id === analysisId);
    if (!analysis) return;
    
    const updatedFindings = analysis.findings.filter(finding => finding.id !== findingId);
    this.updateResult(analysisId, { findings: updatedFindings });
    
    // Recalculate compliance score
    this.updateComplianceScore(analysisId, updatedFindings);
  }
};