<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Card from '$lib/components/common/Card.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import type { ProtocolAnalysisResult, DocumentInfo } from '$lib/types';

  interface Props {
    analysis: ProtocolAnalysisResult;
    groundTruthDocuments: DocumentInfo[];
  }

  let { analysis, groundTruthDocuments }: Props = $props();

  // Svelte 5 runes for state management
  let selectedProtocolIndex = $state<number>(2); // Default to current analysis (index 2)
  let expandedSections = $state<Set<string>>(new Set(['compliance']));
  let showChatInterface = $state<boolean>(false);

  const dispatch = createEventDispatcher<{
    generateReport: { analysis: ProtocolAnalysisResult };
    clearAnalysis: void;
    backToReports: void;
  }>();

  // Derived values - use selected protocol score
  const complianceScore = $derived(
    selectedProtocol.score
  );
  
  const complianceLevel = $derived(() => {
    if (complianceScore >= 80) return 'high';
    if (complianceScore >= 60) return 'medium';
    return 'low';
  });

  const complianceColor = $derived(() => {
    switch (complianceLevel) {
      case 'high': return 'var(--color-success-600)';
      case 'medium': return 'var(--color-warning-600)';
      case 'low': return 'var(--color-error-600)';
      default: return 'var(--color-gray-600)';
    }
  });

  const totalIssues = $derived(
    analysis.compliance_analysis?.compliance_issues?.length || 0
  );
  
  const criticalIssues = $derived(
    analysis.compliance_analysis?.compliance_issues?.filter(issue => issue.severity === 'critical').length || 0
  );
  
  const majorIssues = $derived(
    analysis.compliance_analysis?.compliance_issues?.filter(issue => issue.severity === 'major').length || 0
  );

  const similarSectionsCount = $derived(
    analysis.similar_sections?.length || 0
  );

  const averageSimilarity = $derived(() => {
    if (!analysis.similar_sections || analysis.similar_sections.length === 0) return 0;
    const total = analysis.similar_sections.reduce((sum, section) => sum + section.similarity_score, 0);
    return Math.round((total / analysis.similar_sections.length) * 100);
  });

  // Sample protocols data from the pharmaceutical protocols file
  const protocols = [
    {
      id: 1,
      name: "Amoxicillin 500mg HPLC",
      fullName: "Amoxicillin Tablets 500mg - HPLC Assay Method Validation Protocol",
      score: 78,
      timestamp: "Jan 16, 2024, 10:15 AM",
      content: `# Amoxicillin Tablets 500mg - HPLC Assay Method Validation Protocol

## Product Information
- **Product Name**: Amoxicillin Tablets
- **Strength**: 500 mg  
- **Reference Standards**: USP, European Pharmacopoeia (EP)
- **Method Type**: HPLC-UV for Assay and Related Substances

## Test Method

### HPLC Conditions
- **Column**: Phenomenex Luna C18 (4.6 × 250 mm, 5 μm)
- **Mobile Phase**: Acetonitrile : 0.01M Phosphate Buffer pH 5.0 (15:85 v/v)
- **Flow Rate**: 1.0 mL/min
- **Detection**: UV at 254 nm
- **Injection Volume**: 20 μL
- **Column Temperature**: 25°C
- **Run Time**: 10 minutes

### Sample Preparation
1. Weigh and finely powder not fewer than 20 tablets
2. Transfer accurately weighed portion of powder equivalent to 100 mg amoxicillin to 100 mL volumetric flask
3. Add 70 mL of mobile phase and sonicate for 15 minutes
4. Dilute to volume with mobile phase and mix
5. Filter through 0.45 μm membrane filter
6. Further dilute 5 mL to 50 mL with mobile phase

## Validation Parameters and Acceptance Criteria

### 1. System Suitability
- **Tailing Factor**: NMT 2.0
- **Theoretical Plates**: NLT 2000
- **%RSD of Peak Area** (6 injections): NMT 2.0%
- **Resolution**: NLT 2.0 between amoxicillin and any impurity peak

### 2. Specificity
- **Acceptance Criteria**: No interference from placebo, diluent, or degradation products
- **Forced Degradation Conditions**:
  - Acid: 0.1N HCl at 60°C for 30 minutes
  - Base: 0.1N NaOH at 60°C for 30 minutes  
  - Oxidation: 3% H2O2 at room temperature for 30 minutes
  - Thermal: 105°C for 24 hours
  - Photolytic: UV light (254 nm) for 24 hours

### 3. Linearity
- **Range**: 50% to 150% of working concentration (0.05-0.15 mg/mL)
- **Levels**: 5 (50%, 75%, 100%, 125%, 150%)
- **Acceptance Criteria**: 
  - Correlation coefficient (r²) ≥ 0.999
  - Y-intercept: NMT ±2.0% of 100% response

### 4. Accuracy (Recovery)
- **Levels**: 50%, 100%, 150% (3 preparations each)
- **Acceptance Criteria**: 
  - Individual recovery: 98.0% - 102.0%
  - Mean recovery: 98.0% - 102.0%
  - %RSD: NMT 2.0%

### 5. Precision
- **Repeatability**: 6 determinations at 100% level
  - Acceptance: %RSD NMT 2.0%
- **Intermediate Precision**: Different day, analyst, equipment
  - Acceptance: %RSD NMT 3.0%

### 6. Range
- **Assay Range**: 80% - 120% of label claim
- **Acceptance**: Method meets accuracy, linearity, and precision within this range

### 7. Robustness
- **Parameters to Evaluate**:
  - Mobile phase pH: ±0.2 units
  - Flow rate: ±0.1 mL/min
  - Column temperature: ±5°C
  - Mobile phase composition: ±2%
- **Acceptance**: System suitability criteria met, assay within 98.0-102.0%

### 8. Solution Stability
- **Standard Solution**: Stable for 48 hours at room temperature
- **Sample Solution**: Stable for 24 hours at room temperature
- **Acceptance**: Change in assay value NMT 2.0%

## Related Substances Test

### Acceptance Criteria
- **Amoxicillin Penicilloic Acid**: NMT 1.0%
- **Amoxicillin Penilloic Acid**: NMT 1.0%
- **Any Unspecified Impurity**: NMT 0.5%
- **Total Impurities**: NMT 3.0%

### Limit of Detection/Quantitation
- **LOD**: 0.05% (S/N ratio ≥ 3)
- **LOQ**: 0.15% (S/N ratio ≥ 10, %RSD NMT 10%)`
    },
    {
      id: 2,
      name: "Metformin HCl 500mg",
      fullName: "Metformin HCl Tablets 500mg - Assay and Related Substances",
      score: 92,
      timestamp: "Jan 20, 2024, 10:15 PM",
      content: `# Metformin HCl Tablets 500mg - Assay and Related Substances

## Product Information
- **Product Name**: Metformin Hydrochloride Tablets
- **Strength**: 500 mg
- **Reference**: USP Monograph, EP Monograph
- **Method**: HPLC with UV Detection

## HPLC Method Parameters

### Chromatographic Conditions
- **Column**: Waters Symmetry C18 (4.6 × 150 mm, 3.5 μm)
- **Mobile Phase A**: 10 mM Sodium dihydrogen phosphate buffer pH 3.0
- **Mobile Phase B**: Acetonitrile
- **Gradient Program**:
  - 0-5 min: 95% A, 5% B
  - 5-15 min: 95% A → 50% A
  - 15-20 min: 50% A
  - 20-21 min: 50% A → 95% A
  - 21-30 min: 95% A (re-equilibration)
- **Flow Rate**: 1.2 mL/min
- **Detection**: UV at 218 nm
- **Column Temperature**: 30°C
- **Injection Volume**: 10 μL

### Sample Preparation for Assay
1. Weigh and powder not less than 20 tablets
2. Transfer powder equivalent to 100 mg metformin HCl to 200 mL flask
3. Add 150 mL of water, sonicate for 20 minutes
4. Dilute to volume with water and filter
5. Dilute 5 mL to 100 mL with mobile phase A

## Validation Requirements

### System Suitability (Assay)
- **Retention Time**: Metformin peak at approximately 3.5 minutes
- **Tailing Factor**: NMT 1.5
- **Theoretical Plates**: NLT 5000
- **%RSD** (5 replicate injections): NMT 1.0%

### Specificity
- **Peak Purity**: Purity angle less than purity threshold
- **Placebo Interference**: No peaks at retention time of metformin
- **Known Impurities Resolution**: 
  - Metformin impurity A (Cyanoguanidine): Resolution NLT 2.0
  - Metformin impurity B (1-Methylbiguanide): Resolution NLT 2.0

### Linearity and Range
- **Assay**: 80-120% (400-600 μg/mL)
- **Related Substances**: LOQ to 200% of specification limit
- **Correlation Coefficient**: NLT 0.999
- **Residuals**: Randomly distributed

### Accuracy
- **Levels**: 80%, 100%, 120% (triplicate at each level)
- **Recovery Limits**: 98.5% - 101.5%
- **Overall %RSD**: NMT 1.5%

### Precision
- **Repeatability** (n=6): %RSD NMT 1.0%
- **Intermediate Precision**: %RSD NMT 2.0%
- **Reproducibility**: To be established during method transfer

### Related Substances Limits
- **Cyanoguanidine**: NMT 0.02%
- **1-Methylbiguanide**: NMT 0.05%
- **Any Unspecified Impurity**: NMT 0.10%
- **Total Impurities**: NMT 0.25%

### Detection and Quantitation Limits
- **LOD**: 0.01% (based on S/N = 3)
- **LOQ**: 0.03% (based on S/N = 10)
- **LOQ Precision**: %RSD NMT 5.0%`
    },
    {
      id: 3,
      name: "Current Analysis",
      fullName: "Current Protocol Analysis",
      score: Math.round((analysis.compliance_analysis?.overall_compliance_score || 0) * 100),
      timestamp: new Date(analysis.timestamp).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }),
      content: `# Current Protocol Analysis

This is the current analysis result being displayed from the actual data.`
    },
    {
      id: 4,
      name: "Atorvastatin 20mg",
      fullName: "Atorvastatin Calcium Tablets 20mg - Comprehensive Validation Protocol",
      score: 96,
      timestamp: "Feb 12, 2024, 04:20 PM",
      content: `# Atorvastatin Calcium Tablets 20mg - Comprehensive Validation Protocol

## Product Details
- **Drug Product**: Atorvastatin Calcium Tablets
- **Label Claim**: 20 mg (equivalent to atorvastatin)
- **Pharmacopeial Reference**: USP, Ph. Eur.
- **Analytical Technique**: RP-HPLC with PDA Detection

## Analytical Method

### Chromatographic Parameters
- **Column**: Agilent Zorbax SB-C18 (4.6 × 150 mm, 3.5 μm)
- **Mobile Phase**: 
  - Buffer: 0.1% Phosphoric acid in water
  - Organic: Acetonitrile
  - Ratio: 45:55 (v/v)
- **Flow Rate**: 1.5 mL/min
- **Detection**: 244 nm (PDA detector)
- **Column Temperature**: 35°C
- **Autosampler Temperature**: 5°C
- **Run Time**: 12 minutes

### Standard Preparation
1. Accurately weigh 22 mg of atorvastatin calcium RS
2. Transfer to 100 mL volumetric flask
3. Dissolve in 70 mL of methanol:water (80:20)
4. Sonicate for 10 minutes and dilute to volume
5. Further dilute 5 mL to 25 mL with mobile phase

## Validation Protocol

### 1. System Suitability Requirements
- **Retention Time**: 6.5 ± 0.5 minutes
- **USP Tailing**: NMT 1.5
- **USP Plate Count**: NLT 8000
- **%RSD** (6 injections): NMT 1.0%
- **Resolution** (critical pair): NLT 2.0

### 2. Forced Degradation Study
- **Acid Hydrolysis**: 1N HCl, 80°C, 2 hours (10-20% degradation)
- **Base Hydrolysis**: 1N NaOH, 80°C, 30 min (10-20% degradation)
- **Oxidation**: 10% H2O2, RT, 24 hours (5-15% degradation)
- **Thermal**: 105°C, 48 hours (5-10% degradation)
- **Photolytic**: ICH conditions (5-10% degradation)

### 3. Method Validation Parameters

#### Specificity/Selectivity
- No interference from excipients
- Peak purity index > 0.9999
- Baseline resolution from all degradants

#### Linearity
- **Range**: 25% to 200% of nominal (5-40 μg/mL)
- **Data Points**: 7 levels, duplicate injections
- **Acceptance**: r² ≥ 0.9995, Y-intercept: ±2.0% of 100% response

#### Accuracy
- **Spike Levels**: 50%, 75%, 100%, 125%, 150%
- **Replicates**: n=3 at each level
- **Recovery**: 99.0% - 101.0%
- **Overall RSD**: ≤ 1.5%

#### Precision
- **Repeatability** (n=6): %RSD ≤ 1.0%
- **Intermediate** (2 days, 2 analysts): %RSD ≤ 2.0%
- **Reproducibility**: %RSD ≤ 3.0%

### 4. Related Substances/Impurities
- **Atorvastatin Impurity A**: NMT 0.2%
- **Atorvastatin Impurity B**: NMT 0.2%
- **Atorvastatin Impurity C**: NMT 0.15%
- **Atorvastatin Impurity D**: NMT 0.15%
- **Atorvastatin Lactone**: NMT 0.3%
- **Individual Unspecified**: NMT 0.10%
- **Total Impurities**: NMT 1.0%

### Compliance Requirements
- **ICH Q2(R1) Guidelines**: All validation parameters as per ICH Q2(R1)
- **USP Requirements**: Compendial method verification
- **European Pharmacopoeia**: Compliance with general chapter 2.2.46`
    }
  ];

  // Get the selected protocol
  const selectedProtocol = $derived(protocols[selectedProtocolIndex]);

  // Add full-width class to body when component mounts
  $effect(() => {
    document.body.classList.add('showing-protocol-analysis');
    return () => {
      document.body.classList.remove('showing-protocol-analysis');
    };
  });

  function toggleSection(sectionId: string) {
    if (expandedSections.has(sectionId)) {
      expandedSections.delete(sectionId);
    } else {
      expandedSections.add(sectionId);
    }
    expandedSections = expandedSections; // Trigger reactivity
  }

  function getSeverityColor(severity: string): string {
    switch (severity) {
      case 'critical': 
      case 'non-compliant': return 'var(--color-error-600)';
      case 'major': 
      case 'partially-compliant': return 'var(--color-warning-600)';
      case 'minor': 
      case 'compliant': return 'var(--color-success-600)';
      case 'info': return 'var(--color-primary-600)';
      default: return 'var(--color-gray-600)';
    }
  }

  function getSeverityIcon(severity: string): string {
    switch (severity) {
      case 'critical': 
      case 'non-compliant': return 'x';
      case 'major': 
      case 'partially-compliant': return 'alert-triangle';
      case 'minor': 
      case 'compliant': return 'check';
      case 'info': return 'info';
      default: return 'info';
    }
  }

  function getComplianceLabel(severity: string): string {
    switch (severity) {
      case 'critical': return 'Non-Compliant';
      case 'major': return 'Partially Compliant';
      case 'minor': return 'Compliant';
      case 'info': return 'Compliant';
      default: return severity.toUpperCase();
    }
  }

  function getComplianceClass(severity: string): string {
    switch (severity) {
      case 'critical': return 'non-compliant';
      case 'major': return 'partially-compliant';
      case 'minor': return 'compliant';
      case 'info': return 'compliant';
      default: return severity;
    }
  }

  function formatProcessingTime(timeMs: number): string {
    if (timeMs < 1000) return `${Math.round(timeMs)}ms`;
    return `${(timeMs / 1000).toFixed(2)}s`;
  }

  function generateReport() {
    dispatch('generateReport', { analysis });
  }

  function clearAnalysis() {
    dispatch('clearAnalysis');
  }
  
  function backToReports() {
    dispatch('backToReports');
  }

  function exportAsJSON() {
    const dataStr = JSON.stringify(analysis, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `protocol-analysis-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
</script>

<div class="protocol-analysis-results full-width">
  <!-- Header Section -->
  <div class="page-header">
    <div class="header-left">
      <Button variant="secondary" size="sm" onclick={() => dispatch('backToReports')}>
        <Icon name="arrow-left" size={16} />
        Back to Reports
      </Button>
    </div>
    
    <div class="header-right">
      <Button variant="secondary" size="sm" onclick={exportAsJSON}>
        <Icon name="download" size={16} />
        Export
      </Button>
    </div>
  </div>

  <!-- Compliance Score Cards Row -->
  <div class="score-cards-row">
    {#each protocols as protocol, index}
      <div 
        class="score-card {selectedProtocolIndex === index ? 'highlighted' : ''}"
        onclick={() => selectedProtocolIndex = index}
        role="button"
        tabindex="0"
        onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') selectedProtocolIndex = index; }}
      >
        <div class="score-value">{protocol.score}%</div>
        <div class="score-label">
          <Icon name="calendar" size={12} />
          {protocol.timestamp}
        </div>
        <div class="score-meta">{protocol.name}</div>
      </div>
    {/each}
  </div>

  <!-- Main Compliance Section -->
  <div class="main-compliance-section">
    <div class="compliance-header">
      <div class="compliance-title">
        <Icon name="shield" size={24} />
        {selectedProtocol.fullName}
      </div>
      <div class="compliance-meta">
        <span class="timestamp">
          <Icon name="calendar" size={14} />
          {selectedProtocol.timestamp}
        </span>
        <span class="findings-count">
          <Icon name="clipboard-list" size={14} />
          {totalIssues} findings
        </span>
        <span class="recommendations">
          <Icon name="lightbulb" size={14} />
          {totalIssues} recommendations
        </span>
      </div>
    </div>
    
    <div class="main-score-display">
      <div class="large-score-circle" style="--score-color: {complianceColor}">
        <div class="large-score-value">{complianceScore}%</div>
        <div class="large-score-label">OVERALL COMPLIANCE</div>
      </div>
    </div>
  </div>

  <!-- Two Column Layout -->
  <div class="two-column-layout">
    <!-- Left Column: Protocol Document -->
    <div class="left-column">
      <Card>
        <div class="document-header">
          <h3>Protocol Document</h3>
          <div class="document-status">
            <span class="status-badge compliant">
              <Icon name="check" size={12} />
              Compliant
            </span>
            <span class="status-badge partial">
              <Icon name="alert-triangle" size={12} />
              Partially Compliant
            </span>
            <span class="status-badge non-compliant">
              <Icon name="x" size={12} />
              Non-Compliant
            </span>
          </div>
        </div>
        
        <div class="document-content">
          <!-- Protocol Document Text in Code Block Style -->
          <div class="input-document-label">
            <Icon name="file-text" size={16} />
            Input Document Being Analyzed
          </div>
          <div class="protocol-text-container">
            <pre class="protocol-text-code"><code>{selectedProtocol.content}</code></pre>
          </div>
        </div>
      </Card>
    </div>
    
    <!-- Right Column: Analysis Results -->
    <div class="right-column">
      <Card>
        <div class="results-header">
          <h3>Analysis Results</h3>
        </div>
        
        <!-- Detailed Findings Section -->
        <div class="findings-section">
          <h4>Detailed Findings ({totalIssues})</h4>
          {#if analysis.compliance_analysis?.compliance_issues && analysis.compliance_analysis.compliance_issues.length > 0}
            <div class="findings-list">
              {#each analysis.compliance_analysis.compliance_issues as issue, index}
                <div class="finding-item">
                  <div class="finding-header">
                    <span class="severity-indicator" style="background-color: {getSeverityColor(issue.severity)}">
                      <Icon name="{getSeverityIcon(issue.severity)}" size={12} />
                    </span>
                    <div class="finding-title">
                      <span class="issue-type">{issue.issue_type.replace('_', ' ')}</span>
                      <span class="severity-badge {getComplianceClass(issue.severity)}">{getComplianceLabel(issue.severity)}</span>
                    </div>
                  </div>
                  
                  <div class="finding-content">
                    <h5>Section 2.9.1 - Particulate Contamination</h5>
                    <p class="visible-badge">Visible and sub-visible particle testing</p>
                    <p class="finding-description">{issue.description}</p>
                    {#if issue.suggested_fix}
                      <div class="suggested-action">
                        <Button size="sm" variant="primary">
                          <Icon name="search" size={14} />
                          View in Document
                        </Button>
                      </div>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <div class="no-findings">
              <Icon name="check" size={48} color="var(--color-success-600)" />
              <h4>No Compliance Issues Found</h4>
              <p>Your protocol appears to be well-aligned with ground truth standards.</p>
            </div>
          {/if}
        </div>
        
        <!-- Recommendations Section -->
        <div class="recommendations-section">
          <h4>Recommendations ({totalIssues})</h4>
          <div class="recommendations-list">
            <div class="recommendation-item">
              <div class="recommendation-number">1</div>
              <div class="recommendation-content">
                <p><strong>Implement complete particulate contamination testing program including both microscopic and visible particles</strong></p>
              </div>
            </div>
            <div class="recommendation-item">
              <div class="recommendation-number">2</div>
              <div class="recommendation-content">
                <p><strong>Add missing sterility testing media and extend incubation to 14 days minimum</strong></p>
              </div>
            </div>
            <div class="recommendation-item">
              <div class="recommendation-number">3</div>
              <div class="recommendation-content">
                <p><strong>Increase content uniformity sample size to n=30 for initial validation</strong></p>
              </div>
            </div>
            <div class="recommendation-item">
              <div class="recommendation-number">4</div>
              <div class="recommendation-content">
                <p><strong>Include nickel testing for all polypol recipients with ICP-MS or equivalent method</strong></p>
              </div>
            </div>
            <div class="recommendation-item">
              <div class="recommendation-number">5</div>
              <div class="recommendation-content">
                <p><strong>Consider implementing environmental monitoring program for sterile manufacturing areas</strong></p>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
  
  <!-- AI Compliance Assistant -->
  <div class="ai-assistant-section">
    <Card>
      <!-- Assistant Header with Status Indicators -->
      <div class="assistant-header-new">
        <div class="assistant-title-new">
          <Icon name="message-square" size={20} />
          AI Compliance Assistant
        </div>
        <div class="status-indicators">
          <span class="status-badge analysis-loaded">
            <Icon name="check-circle" size={14} />
            ANALYSIS LOADED
          </span>
          <span class="status-badge context-ready">
            <Icon name="check-circle" size={14} />
            CONTEXT READY
          </span>
        </div>
      </div>

      <!-- Assistant Stats Row -->
      <div class="assistant-stats-new">
        <span class="stat-item">
          <Icon name="file-text" size={14} />
          Document: {Math.ceil(analysis.protocol_input.word_count / 200)} sections analyzed
        </span>
        <span class="stat-item">
          <Icon name="bar-chart-3" size={14} />
          Compliance Score: {complianceScore}%
        </span>
        <span class="stat-item">
          <Icon name="database" size={14} />
          Vector Database: {similarSectionsCount} recommendations indexed
        </span>
      </div>


      <!-- Authentication Section -->
      {#if !showChatInterface}
        <div class="auth-section">
          <div class="auth-content">
            <Icon name="lock" size={48} color="var(--color-gray-400)" />
            <h4>Authentication Required</h4>
            <p>Please sign in to start a conversation with<br>the AI compliance assistant.</p>
            
            <div class="features-section">
              <p class="features-title">With the chat assistant, you can:</p>
              <ul class="features-list">
                <li>Ask questions about compliance findings</li>
                <li>Get recommendations for improvement</li>
                <li>Receive guidance on regulatory standards</li>
              </ul>
            </div>

            <!-- Chat Input Area -->
            <div class="auth-chat-input">
              <div class="input-container">
                <input 
                  type="text" 
                  placeholder="Please sign in to use this" 
                  disabled
                  class="disabled-input"
                />
                <Button variant="primary" onclick={() => showChatInterface = true}>
                  <Icon name="link" size={16} />
                  Connect Document + Analysis
                </Button>
              </div>
            </div>
          </div>
        </div>
      {:else}
        <!-- Active Chat Input -->
        <div class="active-chat-input">
          <div class="input-container">
            <input 
              type="text" 
              placeholder="Ask about compliance findings..." 
              class="active-input"
            />
            <Button variant="primary">
              <Icon name="send" size={16} />
            </Button>
          </div>
        </div>
      {/if}
    </Card>
  </div>
</div>

<style>
  .protocol-analysis-results {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
    max-width: 100%;
    margin: 0 auto;
  }


  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-4) 0;
    border-bottom: 1px solid var(--color-border);
  }

  .score-cards-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--space-4);
    margin: var(--space-6) 0;
  }

  .score-card {
    background: white;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
    text-align: center;
    transition: all var(--transition-fast);
    cursor: pointer;
  }

  .score-card:hover {
    border-color: var(--color-primary-300);
    background: var(--color-gray-50);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .score-card.highlighted {
    border-color: #20B2AA;
    background: #F0F8FF;
  }

  .score-card .score-value {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-text);
    margin-bottom: var(--space-2);
  }

  .score-card .score-label {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    margin-bottom: var(--space-1);
  }

  .score-card .score-meta {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
  }

  .main-compliance-section {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
    color: white;
    border-radius: var(--radius-lg);
    padding: var(--space-8);
    text-align: center;
    margin: var(--space-6) 0;
  }

  .compliance-header {
    margin-bottom: var(--space-6);
  }

  .compliance-title {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-3);
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-4);
  }

  .compliance-meta {
    display: flex;
    justify-content: center;
    gap: var(--space-6);
    font-size: var(--font-size-sm);
    opacity: 0.9;
  }

  .main-score-display {
    display: flex;
    justify-content: center;
  }

  .large-score-circle {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 160px;
    height: 160px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    border: 3px solid rgba(255, 255, 255, 0.3);
  }

  .large-score-value {
    font-size: 3rem;
    font-weight: var(--font-weight-bold);
    line-height: 1;
  }

  .large-score-label {
    font-size: var(--font-size-xs);
    letter-spacing: 0.1em;
    margin-top: var(--space-2);
    opacity: 0.8;
  }

  .two-column-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-6);
    margin: var(--space-6) 0;
  }

  .left-column, .right-column {
    min-height: 600px;
  }

  .document-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-4) var(--space-6);
    border-bottom: 1px solid var(--color-border);
  }

  .document-header h3 {
    margin: 0;
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
  }

  .document-status {
    display: flex;
    gap: var(--space-2);
  }

  .status-badge {
    font-size: var(--font-size-xs);
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    font-weight: var(--font-weight-medium);
  }

  .status-badge.compliant {
    background: #d1fae5;
    color: #065f46;
  }

  .status-badge.partial {
    background: #fef3c7;
    color: #92400e;
  }

  .status-badge.non-compliant {
    background: #fee2e2;
    color: #991b1b;
  }

  .document-content {
    padding: var(--space-6);
  }

  .input-document-label {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text-secondary);
    margin-bottom: var(--space-4);
    padding: var(--space-2) var(--space-3);
    background: var(--color-gray-50);
    border-radius: var(--radius-sm);
    border-left: 3px solid var(--color-primary-500);
  }

  .protocol-text-container {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    overflow: hidden;
    background: var(--color-gray-100);
  }

  .protocol-text-code {
    font-family: 'Fira Code', 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: var(--color-gray-900);
    background: var(--color-gray-100);
    padding: var(--space-6);
    margin: 0;
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  .protocol-text-code code {
    font-family: inherit;
    background: transparent;
    padding: 0;
    color: inherit;
  }

  .protocol-text {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: var(--font-size-sm);
    line-height: var(--line-height-relaxed);
    color: var(--color-text);
  }

  .protocol-text .highlight {
    background: #fef3c7;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    font-weight: var(--font-weight-medium);
  }

  .protocol-text .highlight.critical {
    background: #fee2e2;
    color: #991b1b;
  }

  .protocol-text .highlight.warning {
    background: #fef3c7;
    color: #92400e;
  }

  .protocol-text .highlight.info {
    background: #dbeafe;
    color: #1e40af;
  }

  .protocol-text .compliant-text {
    color: #065f46;
    font-weight: var(--font-weight-medium);
  }

  .protocol-text .requirement-highlight {
    background: #fef3c7;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    font-weight: var(--font-weight-medium);
    color: #92400e;
  }

  .results-header {
    padding: var(--space-4) var(--space-6);
    border-bottom: 1px solid var(--color-border);
  }

  .results-header h3 {
    margin: 0;
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
  }

  .findings-section, .recommendations-section {
    padding: var(--space-6);
  }

  .findings-section h4, .recommendations-section h4 {
    margin: 0 0 var(--space-4) 0;
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
  }

  .findings-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .finding-item {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    overflow: hidden;
  }

  .finding-header {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-4);
    background: var(--color-gray-50);
    border-bottom: 1px solid var(--color-border);
  }

  .severity-indicator {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: var(--font-size-xs);
    flex-shrink: 0;
  }

  .finding-title {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    flex: 1;
  }

  .issue-type {
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
  }

  .severity-badge {
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
  }

  .severity-badge.non-compliant {
    background: #fee2e2;
    color: #991b1b;
  }

  .severity-badge.partially-compliant {
    background: #fef3c7;
    color: #92400e;
  }

  .severity-badge.compliant {
    background: #d1fae5;
    color: #065f46;
  }

  /* Legacy severity classes for backward compatibility */
  .severity-badge.critical {
    background: #fee2e2;
    color: #991b1b;
  }

  .severity-badge.major {
    background: #fef3c7;
    color: #92400e;
  }

  .severity-badge.minor {
    background: #dbeafe;
    color: #1e40af;
  }

  .finding-content {
    padding: var(--space-4);
  }

  .finding-content h5 {
    margin: 0 0 var(--space-2) 0;
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text);
  }

  .visible-badge {
    display: inline-block;
    background: #dbeafe;
    color: #1e40af;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    margin-bottom: var(--space-2);
  }

  .finding-description {
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0 0 var(--space-3) 0;
  }

  .suggested-action {
    margin-top: var(--space-3);
  }

  .recommendations-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .recommendation-item {
    display: flex;
    gap: var(--space-3);
    padding: var(--space-3);
    background: #f0f9ff;
    border-radius: var(--radius-md);
  }

  .recommendation-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    background: #3b82f6;
    color: white;
    border-radius: 50%;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-bold);
    flex-shrink: 0;
  }

  .recommendation-content {
    flex: 1;
  }

  .recommendation-content p {
    margin: 0;
    font-size: var(--font-size-sm);
    color: var(--color-text);
  }

  .ai-assistant-section {
    margin-top: var(--space-6);
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
  }

  /* Compact Professional Header */
  .assistant-header-new {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-3) var(--space-4);
    border-bottom: 1px solid var(--color-border);
    background: var(--color-gray-50);
  }

  .assistant-title-new {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    color: var(--color-primary-700);
  }

  .status-indicators {
    display: flex;
    gap: var(--space-2);
  }

  .status-badge {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    padding: 2px var(--space-2);
    border-radius: var(--radius-sm);
    font-size: 10px;
    font-weight: var(--font-weight-medium);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .status-badge.analysis-loaded,
  .status-badge.context-ready {
    background: #d1fae5;
    color: #065f46;
  }

  /* Compact Assistant Stats */
  .assistant-stats-new {
    display: flex;
    justify-content: space-between;
    padding: var(--space-2) var(--space-4);
    background: #f8fafc;
    border-bottom: 1px solid var(--color-border);
    font-size: var(--font-size-xs);
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    color: var(--color-primary-600);
    font-weight: var(--font-weight-medium);
  }



  /* Compact Authentication Section */
  .auth-section {
    padding: var(--space-4);
    margin-top: var(--space-2);
  }

  .auth-content {
    text-align: center;
    max-width: 400px;
    margin: 0 auto;
  }

  .auth-content h4 {
    margin: var(--space-2) 0 var(--space-1) 0;
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text);
  }

  .auth-content > p {
    color: var(--color-text-secondary);
    line-height: var(--line-height-normal);
    margin-bottom: var(--space-3);
    font-size: var(--font-size-sm);
  }

  .features-section {
    margin: var(--space-3) 0;
  }

  .features-title {
    font-weight: var(--font-weight-medium);
    margin-bottom: var(--space-1);
    color: var(--color-text);
    font-size: var(--font-size-sm);
  }

  .features-list {
    text-align: left;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .features-list li {
    color: var(--color-text-secondary);
    margin-bottom: 2px;
    padding-left: var(--space-3);
    position: relative;
    font-size: var(--font-size-sm);
  }

  .features-list li::before {
    content: '•';
    color: var(--color-primary-500);
    position: absolute;
    left: 0;
    font-weight: bold;
  }

  /* Compact Input Areas */
  .auth-chat-input,
  .active-chat-input {
    margin-top: var(--space-3);
  }

  .input-container {
    display: flex;
    gap: var(--space-2);
    align-items: center;
    padding: var(--space-2);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: white;
  }

  .disabled-input,
  .active-input {
    flex: 1;
    padding: var(--space-2);
    border: none;
    background: transparent;
    font-size: var(--font-size-sm);
    outline: none;
  }

  .disabled-input {
    color: var(--color-text-muted);
    cursor: not-allowed;
  }

  .active-input {
    color: var(--color-text);
  }

  .active-input:focus {
    outline: none;
  }

  .input-container:focus-within {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .no-findings {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-8);
    text-align: center;
  }

  .no-findings h4 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .no-findings p {
    color: var(--color-text-secondary);
    margin: 0;
    line-height: var(--line-height-relaxed);
  }

  @media (max-width: 1200px) {
    .two-column-layout {
      grid-template-columns: 1fr;
      gap: var(--space-4);
    }
    
    .left-column {
      order: 2;
    }
    
    .right-column {
      order: 1;
    }
  }

  @media (max-width: 768px) {
    .score-cards-row {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .page-header {
      flex-direction: column;
      gap: var(--space-4);
      align-items: stretch;
    }
    
    .compliance-meta {
      flex-direction: column;
      gap: var(--space-2);
    }
    
    .assistant-header {
      flex-direction: column;
      gap: var(--space-3);
      align-items: flex-start;
    }
    
    .assistant-stats {
      flex-direction: column;
      gap: var(--space-1);
    }
  }

  @media (max-width: 480px) {
    .score-cards-row {
      grid-template-columns: 1fr;
    }
    
    .main-compliance-section {
      padding: var(--space-6);
    }
    
    .large-score-circle {
      width: 120px;
      height: 120px;
    }
    
    .large-score-value {
      font-size: 2rem;
    }
  }
</style>