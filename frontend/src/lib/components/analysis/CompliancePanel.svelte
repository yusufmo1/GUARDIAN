<script lang="ts">
  import type { AnalysisResult, ComplianceFinding } from '$lib/types';
  import Icon from '$lib/components/common/Icon.svelte';
  import Card from '$lib/components/common/Card.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import { getComplianceColor, getSeverityColor, getComplianceScoreClass } from '$lib/utils';
  import { STATUS_LABELS, SEVERITY_LABELS } from '$lib/constants';

  interface Props {
    analysis: AnalysisResult;
    expanded?: boolean;
  }
  
  let { analysis, expanded = false }: Props = $props();

  // Convert reactive statements to Svelte 5 $derived
  const findings = $derived(analysis.findings || []);
  const complianceClass = $derived(getComplianceScoreClass(analysis.complianceScore));
  const criticalFindings = $derived(findings.filter(f => f.severity === 'critical'));
  const nonCompliantFindings = $derived(findings.filter(f => f.status === 'non-compliant'));
  
  // Additional derived computations for enhanced UX
  const warningFindings = $derived(findings.filter(f => f.severity === 'warning'));
  const infoFindings = $derived(findings.filter(f => f.severity === 'info'));

  function toggleExpanded() {
    expanded = !expanded;
  }

  function getFindingIcon(status: string): string {
    switch (status) {
      case 'compliant': return 'check';
      case 'non-compliant': return 'x';
      case 'partial': return 'warning';
      case 'needs-review': return 'info';
      default: return 'info';
    }
  }
</script>

<Card padding="lg">
  <div class="compliance-panel">
    <div class="panel-header">
      <div class="header-main">
        <h3 class="panel-title">Compliance Analysis</h3>
        <div class="compliance-score {complianceClass}">
          <Icon name="analysis" size={20} />
          <span class="score-value">{analysis.complianceScore}%</span>
          <span class="score-label">Compliant</span>
        </div>
      </div>
      
      <div class="header-stats">
        <div class="stat">
          <span class="stat-value">{findings.length}</span>
          <span class="stat-label">Total Findings</span>
        </div>
        <div class="stat">
          <span class="stat-value">{criticalFindings.length}</span>
          <span class="stat-label">Critical</span>
        </div>
        <div class="stat">
          <span class="stat-value">{nonCompliantFindings.length}</span>
          <span class="stat-label">Non-Compliant</span>
        </div>
      </div>

      <Button
        variant="secondary"
        size="sm"
        onclick={toggleExpanded}
      >
        <Icon name={expanded ? 'arrow-up' : 'arrow-down'} size={16} />
        {expanded ? 'Hide Details' : 'Show Details'}
      </Button>
    </div>

    <div class="progress-bar">
      <div 
        class="progress-fill {complianceClass}"
        style="width: {analysis.complianceScore}%"
      ></div>
    </div>

    {#if expanded}
      <div class="panel-content">
        <!-- Findings Section -->
        {#if findings.length > 0}
          <div class="findings-section">
            <h4 class="section-title">
              <Icon name="info" size={16} />
              Detailed Findings ({findings.length})
            </h4>
            
            <div class="findings-list">
              {#each findings as finding (finding.id)}
                <div class="finding-item">
                  <div class="finding-header">
                    <div class="finding-status">
                      <Icon 
                        name={getFindingIcon(finding.status)} 
                        size={16} 
                        color={getComplianceColor(finding.status)}
                      />
                      <span 
                        class="status-label"
                        style="color: {getComplianceColor(finding.status)}"
                      >
                        {STATUS_LABELS[finding.status]}
                      </span>
                    </div>
                    
                    <div class="finding-severity">
                      <span 
                        class="severity-badge"
                        style="background-color: {getSeverityColor(finding.severity)}20; color: {getSeverityColor(finding.severity)}"
                      >
                        {SEVERITY_LABELS[finding.severity]}
                      </span>
                    </div>
                  </div>

                  <div class="finding-content">
                    <h5 class="finding-section">{finding.section}</h5>
                    <p class="finding-requirement">{finding.requirement}</p>
                    <p class="finding-description">{finding.description}</p>
                    
                    {#if finding.reference}
                      <div class="finding-reference">
                        <Icon name="file" size={14} />
                        <span>Reference: {finding.reference}</span>
                      </div>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Recommendations Section -->
        {#if analysis.recommendations && analysis.recommendations.length > 0}
          <div class="recommendations-section">
            <h4 class="section-title">
              <Icon name="info" size={16} />
              Recommendations ({analysis.recommendations.length})
            </h4>
            
            <div class="recommendations-list">
              {#each analysis.recommendations as recommendation, index}
                <div class="recommendation-item">
                  <div class="recommendation-number">{index + 1}</div>
                  <p class="recommendation-text">{recommendation}</p>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</Card>

<style>
  .compliance-panel {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .panel-header {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .header-main {
    display: flex;
    justify-content: between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--space-4);
  }

  .panel-title {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text);
    margin: 0;
  }

  .compliance-score {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-full);
    font-weight: var(--font-weight-medium);
  }

  .compliance-score.high {
    background: var(--color-success-50);
    color: var(--color-success-700);
    border: 1px solid var(--color-success-200);
  }

  .compliance-score.medium {
    background: var(--color-warning-50);
    color: var(--color-warning-700);
    border: 1px solid var(--color-warning-200);
  }

  .compliance-score.low {
    background: var(--color-error-50);
    color: var(--color-error-700);
    border: 1px solid var(--color-error-200);
  }

  .score-value {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-bold);
  }

  .header-stats {
    display: flex;
    gap: var(--space-6);
    align-items: center;
  }

  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-1);
  }

  .stat-value {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-bold);
    color: var(--color-text);
  }

  .stat-label {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    text-transform: uppercase;
    font-weight: var(--font-weight-medium);
  }

  .progress-bar {
    width: 100%;
    height: 12px;
    background: var(--color-gray-200);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    border-radius: var(--radius-full);
    transition: width var(--transition-normal);
  }

  .progress-fill.high {
    background: var(--color-success-500);
  }

  .progress-fill.medium {
    background: var(--color-warning-500);
  }

  .progress-fill.low {
    background: var(--color-error-500);
  }

  .panel-content {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
    padding-top: var(--space-4);
    border-top: 1px solid var(--color-border);
  }

  .section-title {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin-bottom: var(--space-4);
  }

  .findings-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .finding-item {
    padding: var(--space-4);
    background: var(--color-gray-50);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
  }

  .finding-header {
    display: flex;
    justify-content: between;
    align-items: center;
    margin-bottom: var(--space-3);
    flex-wrap: wrap;
    gap: var(--space-2);
  }

  .finding-status {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  .status-label {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
  }

  .severity-badge {
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    text-transform: uppercase;
  }

  .finding-content {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .finding-section {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-semibold);
    color: var(--color-primary-600);
    margin: 0;
  }

  .finding-requirement {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin: 0;
  }

  .finding-description {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0;
  }

  .finding-reference {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    margin-top: var(--space-2);
  }

  .recommendations-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .recommendation-item {
    display: flex;
    gap: var(--space-3);
    align-items: flex-start;
  }

  .recommendation-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    background: var(--color-primary-100);
    color: var(--color-primary-600);
    border-radius: var(--radius-full);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    flex-shrink: 0;
  }

  .recommendation-text {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0;
  }

  @media (max-width: 768px) {
    .header-main {
      flex-direction: column;
      align-items: flex-start;
    }

    .header-stats {
      gap: var(--space-4);
    }

    .finding-header {
      flex-direction: column;
      align-items: flex-start;
    }
  }
</style>