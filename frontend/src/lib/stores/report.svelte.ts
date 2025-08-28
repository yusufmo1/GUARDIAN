import { browser } from '$app/environment';
import { api } from '$lib/services/api';
import type { Report, ReportFormat, ReportGenerationRequest } from '$lib/types';

/**
 * Report Store - Svelte 5 Runes Edition
 * Manages report generation, storage, and retrieval
 */

interface ReportState {
  reports: Map<string, Report>;
  generatingReports: Set<string>;
  error: string | null;
  lastUpdated: number;
}

class ReportStore {
  // Private state with $state rune
  private state = $state<ReportState>({
    reports: new Map(),
    generatingReports: new Set(),
    error: null,
    lastUpdated: Date.now()
  });

  // Public getters
  get reports() {
    return Array.from(this.state.reports.values());
  }

  get reportCount() {
    return this.state.reports.size;
  }

  get isGenerating() {
    return this.state.generatingReports.size > 0;
  }

  get generatingCount() {
    return this.state.generatingReports.size;
  }

  get error() {
    return this.state.error;
  }

  // Derived values
  get hasReports() {
    return this.state.reports.size > 0;
  }

  get recentReports() {
    return this.reports
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
      .slice(0, 10);
  }

  get reportsByFormat() {
    const byFormat = new Map<ReportFormat, Report[]>();
    
    this.reports.forEach(report => {
      const format = report.format;
      if (!byFormat.has(format)) {
        byFormat.set(format, []);
      }
      byFormat.get(format)!.push(report);
    });
    
    return byFormat;
  }

  get totalReportSize() {
    return this.reports.reduce((total, report) => total + (report.size || 0), 0);
  }

  // Actions
  async generateReport(request: ReportGenerationRequest): Promise<Report | null> {
    const tempId = `temp-${Date.now()}`;
    this.state.generatingReports.add(tempId);
    this.state.error = null;

    try {
      const response = await api.post<Report>('/api/reports/generate', request);
      
      if (response.data) {
        const report = response.data;
        this.state.reports.set(report.id, report);
        this.state.lastUpdated = Date.now();
        return report;
      }
      
      throw new Error('No data received from server');
    } catch (error) {
      console.error('Failed to generate report:', error);
      this.state.error = error instanceof Error ? error.message : 'Failed to generate report';
      return null;
    } finally {
      this.state.generatingReports.delete(tempId);
    }
  }

  async fetchReports(): Promise<void> {
    try {
      const response = await api.get<Report[]>('/api/reports');
      
      if (response.data) {
        this.state.reports.clear();
        response.data.forEach(report => {
          this.state.reports.set(report.id, report);
        });
        this.state.lastUpdated = Date.now();
      }
    } catch (error) {
      console.error('Failed to fetch reports:', error);
      this.state.error = error instanceof Error ? error.message : 'Failed to fetch reports';
    }
  }

  async downloadReport(reportId: string): Promise<Blob | null> {
    try {
      const response = await fetch(`/api/reports/${reportId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to download report: ${response.statusText}`);
      }

      return await response.blob();
    } catch (error) {
      console.error('Failed to download report:', error);
      this.state.error = error instanceof Error ? error.message : 'Failed to download report';
      return null;
    }
  }

  async deleteReport(reportId: string): Promise<boolean> {
    try {
      await api.delete(`/api/reports/${reportId}`);
      this.state.reports.delete(reportId);
      this.state.lastUpdated = Date.now();
      return true;
    } catch (error) {
      console.error('Failed to delete report:', error);
      this.state.error = error instanceof Error ? error.message : 'Failed to delete report';
      return false;
    }
  }

  updateGenerationProgress(reportId: string, progress: number, stage: string): void {
    const report = this.state.reports.get(reportId);
    if (report) {
      report.generationProgress = progress;
      report.generationStage = stage;
      this.state.lastUpdated = Date.now();
    }
  }

  refreshReports(): void {
    this.fetchReports();
  }

  clearError(): void {
    this.state.error = null;
  }

  reset(): void {
    this.state.reports.clear();
    this.state.generatingReports.clear();
    this.state.error = null;
    this.state.lastUpdated = Date.now();
  }

  // Initialize store
  initialize(): void {
    if (!browser) return;
    
    // Fetch reports on initialization if authenticated
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.fetchReports();
    }
  }
}

// Export singleton instance
export const reportStore = new ReportStore();

// Export derived states
export const hasReports = $derived(reportStore.hasReports);
export const reportCount = $derived(reportStore.reportCount);
export const isGeneratingReport = $derived(reportStore.isGenerating);
export const generatingCount = $derived(reportStore.generatingCount);
export const recentReports = $derived(reportStore.recentReports);
export const reportsByFormat = $derived(reportStore.reportsByFormat);
export const totalReportSize = $derived(reportStore.totalReportSize);
export const reportError = $derived(reportStore.error);