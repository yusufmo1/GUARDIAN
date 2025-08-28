<script lang="ts">
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import Button from '$lib/components/common/Button.svelte';
  import Card from '$lib/components/common/Card.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import ProtocolAnalysisResults from '$lib/components/analysis/ProtocolAnalysisResults.svelte';
  import { authState } from '$lib/stores';
  import { formatDate, getComplianceScoreClass } from '$lib/utils';
  import type { AnalysisResult, ComplianceFinding, ProtocolAnalysisResult, DocumentInfo } from '$lib/types';

  // Modern Svelte 5 state management with all original functionality
  let selectedAnalysis = $state<AnalysisResult | null>(null);
  let showAnalysis = $state(false);

  // Reactive authentication state
  const authenticated = $derived(authState.authenticated);

  // Complete original sample data preserved exactly
  const SAMPLE_REPORTS: AnalysisResult[] = [
    {
      id: '1',
      documentId: 'doc1',
      status: 'completed',
      complianceScore: 78,
      documentText: `ANALYTICAL METHOD VALIDATION PROTOCOL
AMOXICILLIN TABLETS 500mg - HPLC ASSAY METHOD

1. INTRODUCTION
This protocol describes the validation of an HPLC-UV analytical method for the determination of amoxicillin content in 500mg film-coated tablets according to USP monograph requirements, EMA validation guidelines, and ICH Q2(R1) standards.

2. ANALYTICAL METHOD SPECIFICATIONS

2.1 IDENTIFICATION (Section 2.2.1)
The active pharmaceutical ingredient shall be identified using HPLC retention time comparison and UV spectral analysis at 254nm. Peak purity assessment using photodiode array detection confirms specificity.

2.2 CHROMATOGRAPHIC CONDITIONS (Section 2.2.46)
- Column: C18, 250 × 4.6 mm, 5 μm particle size
- Mobile phase: Phosphate buffer pH 5.0 : Acetonitrile (95:5)
- Flow rate: 1.0 mL/min
- Detection: UV at 254nm
- Injection volume: 20 μL
- Runtime: 15 minutes

HPLC system suitability parameters:
- Resolution between amoxicillin and nearest impurity: ≥2.0
- Tailing factor: ≤2.0
- Theoretical plates: ≥2000
- Relative standard deviation: ≤2.0% (n=6 injections)

2.3 RELATED SUBSTANCES ANALYSIS (Section 2.2.3)
Impurity profile by gradient HPLC:
- Amoxicilloic acid: ≤0.5%
- Individual unspecified impurities: ≤0.2%
- Total impurities: ≤3.0%
- Reporting threshold: ≥0.05%

Current testing shows some degradation products above limits during accelerated conditions.

2.4 VALIDATION PARAMETERS
Method validation completed according to ICH Q2(R1):
- Linearity: r² = 0.9995 (50-150% range)
- Accuracy: 99.2-101.1% recovery
- Precision: %RSD = 0.8% (repeatability)
- LOD: 0.03 μg/mL
- LOQ: 0.10 μg/mL

Missing: Intermediate precision data not yet collected.

2.5 SOLUTION STABILITY
Standard solution stable for 24 hours at room temperature. Sample solution stability requires verification beyond 6 hours.

3. DISSOLUTION TEST (Section 2.9.3)
- Apparatus: USP Type 2 (Paddle)
- Medium: 900 mL phosphate buffer pH 6.8
- Speed: 75 rpm
- Acceptance: Q = 80% in 30 minutes
- Current results: 85-92% in 30 minutes (compliant)

4. MICROBIOLOGICAL QUALITY (Section 2.6.12)
Total aerobic microbial count: ≤10³ CFU/g
Total yeast and mold count: ≤10² CFU/g
Absence of E. coli and Salmonella confirmed

Testing frequency currently quarterly but FDA guidance requires monthly testing for Category 3 OTC preparations.`,
      findings: [
        {
          id: 'f1',
          section: 'Section 2.2.1 - Identification',
          requirement: 'Analytical method validation',
          status: 'compliant',
          description: 'The analytical method is properly validated according to ICH Q2(R1) guidelines with acceptable precision, accuracy, and linearity.',
          severity: 'info',
        },
        {
          id: 'f2',
          section: 'Section 2.4.8 - Heavy Metals',
          requirement: 'Heavy metal limits testing',
          status: 'non-compliant',
          description: 'Heavy metal testing documentation is incomplete. EP requires limits for lead (≤5ppm), mercury (≤0.1ppm), cadmium (≤1ppm), and arsenic (≤1.5ppm).',
          severity: 'critical',
        },
        {
          id: 'f3',
          section: 'Section 2.6.12 - Microbial Contamination',
          requirement: 'Microbial testing protocols',
          status: 'partial',
          description: 'Microbiological testing documented but frequency (quarterly) does not meet FDA guidance requirement of monthly testing for Category 3 OTC preparations.',
          severity: 'major',
        },
        {
          id: 'f4',
          section: 'Section 2.2.46 - Chromatographic Separation',
          requirement: 'System suitability criteria',
          status: 'compliant',
          description: 'HPLC system suitability parameters properly defined: resolution >2.0, tailing factor <2.0, theoretical plates >2000.',
          severity: 'info',
        },
      ],
      recommendations: [
        'Implement comprehensive heavy metal testing protocol according to EP Chapter 2.4.8',
        'Increase microbial testing frequency from monthly to weekly for Category 3 preparations',
        'Add accelerated stability studies at 40°C/75% RH for 6 months minimum',
        'Include forced degradation studies to identify potential degradation products',
      ],
      createdAt: new Date('2025-01-15T10:30:00'),
      completedAt: new Date('2025-01-15T10:35:00'),
    },
    {
      id: '2',
      documentId: 'doc2',
      status: 'completed',
      complianceScore: 92,
      documentText: `QUALITY CONTROL SPECIFICATION
ATORVASTATIN CALCIUM TABLETS 20mg

1. GENERAL REQUIREMENTS (Section 2.1.1)
This specification covers all quality control requirements for Atorvastatin Calcium tablets 20mg manufactured according to EP, FDA, and MHRA standards for global distribution. All documentation is complete including specifications, analytical procedures, validation reports, and stability data.

2. IDENTIFICATION AND PURITY TESTING

2.1 RELATED SUBSTANCES (Section 2.2.3)
Comprehensive impurity profiling has been established:
- Individual impurities: ≤0.1%
- Total impurities: ≤0.5%
- Specified degradation products monitored by HPLC

2.2 DISINTEGRATION TEST (Section 2.9.1)
Tablet disintegration test parameters:
- Medium: Water at 37°C ± 2°C
- Acceptance criteria: All tablets disintegrate within 15 minutes
- Equipment: USP Apparatus (6 tubes, mesh #10)

3. PHYSICAL TESTING

3.1 STORAGE CONDITIONS (Section 2.2.7)
Storage conditions are specified as 25°C/60% RH for long-term stability. Real-time stability data available for 18 months. Accelerated stability studies are currently at 3 months (40°C/75% RH) and require completion to 6 months to support 24-month shelf life claim.

4. ANALYTICAL METHODS
All analytical methods have been validated according to ICH guidelines with appropriate precision, accuracy, and specificity demonstrated.

5. BATCH RELEASE CRITERIA
All critical quality attributes have been defined with appropriate acceptance criteria based on clinical and stability data.`,
      findings: [
        {
          id: 'f5',
          section: 'Section 2.1.1 - General Requirements',
          requirement: 'Documentation completeness',
          status: 'compliant',
          description: 'All required EP, FDA, and MHRA documentation complete: specifications, analytical procedures, validation reports, and stability data.',
          severity: 'info',
        },
        {
          id: 'f6',
          section: 'Section 2.2.3 - Related Substances',
          requirement: 'Impurity profiling and limits',
          status: 'compliant',
          description: 'Comprehensive impurity profiling documented with appropriate limits: individual impurities ≤0.1%, total impurities ≤0.5%.',
          severity: 'info',
        },
        {
          id: 'f7',
          section: 'Section 2.9.1 - Disintegration Test',
          requirement: 'Tablet disintegration criteria',
          status: 'compliant',
          description: 'Disintegration test properly documented: all tablets disintegrate within 15 minutes in water at 37°C ± 2°C.',
          severity: 'info',
        },
        {
          id: 'f8',
          section: 'Section 2.2.7 - Storage Conditions',
          requirement: 'Long-term stability data',
          status: 'partial',
          description: 'Storage conditions specified (25°C/60% RH) but accelerated stability data incomplete - only 3 months available, ICH Q1A(R2) requires 6 months for FDA and EMA submissions.',
          severity: 'major',
        },
      ],
      recommendations: [
        'Complete accelerated stability studies to 6 months per ICH Q1A(R2) to support 24-month shelf life claim for FDA and EMA',
        'Consider implementing real-time stability program with annual testing',
        'Add photostability testing according to ICH Q1B guidelines for global regulatory compliance',
      ],
      createdAt: new Date('2025-01-20T14:15:00'),
      completedAt: new Date('2025-01-20T14:20:00'),
    },
    {
      id: '3',
      documentId: 'doc3',
      status: 'completed',
      complianceScore: 65,
      documentText: `INJECTABLE SOLUTION PROTOCOL
MORPHINE SULFATE 10mg/mL INJECTION

1. PRODUCT SPECIFICATIONS
Sterile solution for injection containing morphine sulfate 10mg per mL in water for injection.

2. IDENTIFICATION TESTING (Section 2.2.24)
Active pharmaceutical ingredient identification:
- Method: IR spectroscopy
- Acceptance: Correlation coefficient >0.99 with reference standard
- Status: Compliant - proper identification confirmed

3. PARTICULATE CONTAMINATION (Section 2.5.1)
Injectable solutions require both visible and sub-visible particle testing according to European Pharmacopoeia. Current documentation does not include particulate contamination testing protocols.

4. STERILITY TESTING (Section 2.6.1)
Sterility assurance protocols:
- Current testing uses Fluid Thioglycollate medium
- Missing: Soybean-Casein Digest medium testing
- Incubation period: Currently 7 days (requires 14 days minimum)

5. CONTENT UNIFORMITY (Section 2.9.40)
Uniformity of dosage units testing:
- Current sample size: n=10
- EP requirement: n=30 for initial validation
- High variability observed (RSD 4.8%)

6. TRACE METAL ANALYSIS (Section 2.4.25)
Polyol excipients require nickel testing:
- EP limit: ≤1ppm for pharmaceutical grade polyols
- Current status: Not documented
- Required method: ICP-MS or equivalent

7. PYROGEN TESTING (Section 2.8.1)
Bacterial endotoxin testing for injectable formulations:
- EP requirement: LAL test with limit ≤5 EU/kg body weight
- Current status: Not documented

8. MANUFACTURING CONTROLS
Environmental monitoring program for sterile manufacturing areas requires implementation to ensure product quality and patient safety.`,
      findings: [
        {
          id: 'f9',
          section: 'Section 2.5.1 - Particulate Contamination',
          requirement: 'Visible and sub-visible particle testing',
          status: 'non-compliant',
          description: 'Particulate contamination testing missing for injectable solution. EP requires both visible and sub-visible particle testing.',
          severity: 'critical',
        },
        {
          id: 'f10',
          section: 'Section 2.6.1 - Sterility Testing',
          requirement: 'Sterility assurance protocols',
          status: 'partial',
          description: 'Sterility testing documented but does not include all required growth media (Fluid Thioglycollate and Soybean-Casein Digest).',
          severity: 'critical',
        },
        {
          id: 'f11',
          section: 'Section 2.2.24 - Identification Reaction',
          requirement: 'API identification tests',
          status: 'compliant',
          description: 'Active pharmaceutical ingredient properly identified using IR spectroscopy with acceptable correlation coefficient >0.99.',
          severity: 'info',
        },
        {
          id: 'f12',
          section: 'Section 2.9.40 - Uniformity of Dosage Units',
          requirement: 'Content uniformity testing',
          status: 'partial',
          description: 'Content uniformity tested but sample size (n=10) below EP requirement of n=30 for initial validation.',
          severity: 'major',
        },
        {
          id: 'f13',
          section: 'Section 2.4.25 - Nickel in Polyols',
          requirement: 'Trace metal analysis',
          status: 'non-compliant',
          description: 'Nickel testing not documented for polyol excipients. EP limit is ≤1ppm for pharmaceutical grade polyols.',
          severity: 'major',
        },
      ],
      recommendations: [
        'Implement complete particulate contamination testing program including light obscuration and microscopic methods',
        'Add missing sterility testing media and extend incubation to 14 days minimum',
        'Increase content uniformity sample size to n=30 for validation studies',
        'Include nickel testing for all polyol excipients with ICP-MS or equivalent method',
        'Consider implementing environmental monitoring program for sterile manufacturing areas',
      ],
      createdAt: new Date('2025-02-05T09:45:00'),
      completedAt: new Date('2025-02-05T09:52:00'),
    },
    {
      id: '4',
      documentId: 'doc4',
      status: 'completed',
      complianceScore: 96,
      documentText: `PHARMACEUTICAL QUALITY SPECIFICATIONS
INSULIN HUMAN INJECTION 100 IU/mL

1. PRODUCT OVERVIEW
Human insulin injection for subcutaneous administration, manufactured according to highest pharmaceutical standards.

2. COLOR SPECIFICATION (Section 2.2.2)
Color specification properly defined using European Pharmacopoeia reference standards:
- Acceptance criteria: Colorless to slightly yellow solution
- Reference: EP Color Reference Standards
- Tolerance: Within acceptable ranges as defined

3. HEAVY METALS TESTING (Section 2.2.4)
Lead content testing by atomic absorption spectroscopy:
- Method: Atomic absorption spectroscopy
- Detection limit: 0.1ppm
- EP limit: 5ppm for pharmaceutical preparations
- Status: Validated and compliant

4. DISSOLUTION TESTING (Section 2.9.3)
Drug release specifications for modified-release formulations:
- Apparatus: USP Apparatus 2 (paddle method)
- Speed: 50 rpm
- Medium: pH 6.8 phosphate buffer
- Acceptance criteria: Q=80% in 30 minutes
- Status: Validated with appropriate acceptance criteria

5. PROTEIN CHARACTERIZATION (Section 2.2.56)
Amino acid analysis for protein characterization:
- Method: Post-column derivatization HPLC
- Current precision: RSD 3.2%
- Target precision: <2.0% RSD
- Status: Method optimization recommended for improved precision

6. QUALITY ASSURANCE
All critical quality parameters meet or exceed European Pharmacopoeia requirements. Comprehensive quality control program ensures consistent product quality and patient safety.`,
      findings: [
        {
          id: 'f14',
          section: 'Section 2.2.2 - Degree of Coloration',
          requirement: 'Color specification and testing',
          status: 'compliant',
          description: 'Color specification properly defined using European Pharmacopoeia reference standards with acceptable tolerance ranges.',
          severity: 'info',
        },
        {
          id: 'f15',
          section: 'Section 2.2.4 - Heavy Metals Method A',
          requirement: 'Lead testing by atomic absorption',
          status: 'compliant',
          description: 'Lead content testing validated using atomic absorption spectroscopy with detection limit 0.1ppm, well below EP limit of 5ppm.',
          severity: 'info',
        },
        {
          id: 'f16',
          section: 'Section 2.9.3 - Dissolution Test',
          requirement: 'Drug release specifications',
          status: 'compliant',
          description: 'Dissolution test validated with appropriate acceptance criteria: Q=80% in 30 minutes using USP Apparatus 2 at 50 rpm.',
          severity: 'info',
        },
        {
          id: 'f17',
          section: 'Section 2.2.56 - Amino Acid Analysis',
          requirement: 'Protein characterization',
          status: 'partial',
          description: 'Amino acid composition determined but quantitative analysis precision could be improved (current RSD 3.2%, target <2.0%).',
          severity: 'minor',
        },
      ],
      recommendations: [
        'Optimize amino acid analysis method to achieve RSD <2.0% for improved precision',
        'Consider implementing automated dissolution testing for increased throughput',
        'Add comparative dissolution studies with reference product',
      ],
      createdAt: new Date('2025-02-12T16:20:00'),
      completedAt: new Date('2025-02-12T16:25:00'),
    }
  ];

  function selectAnalysis(analysis: AnalysisResult) {
    selectedAnalysis = analysis;
    showAnalysis = true;
  }

  function backToReports() {
    showAnalysis = false;
    selectedAnalysis = null;
  }

  function downloadReport(analysis: AnalysisResult) {
    // This is a sample report, just show a message
    if (typeof window !== 'undefined') {
      alert('This is a sample report. Sign in to generate and download real compliance reports.');
    }
  }

  function signInToStart() {
    goto('/login?redirect=/protocols');
  }

  // Handle ESC key to close analysis view
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && showAnalysis) {
      backToReports();
    }
  }

  // Convert AnalysisResult to ProtocolAnalysisResult format for the new component
  function convertToProtocolAnalysisResult(analysis: AnalysisResult): ProtocolAnalysisResult {
    return {
      timestamp: analysis.createdAt.toISOString(),
      processing_time: 5.2, // Mock processing time
      protocol_input: {
        word_count: analysis.documentText.split(' ').length,
        character_count: analysis.documentText.length
      },
      compliance_analysis: {
        overall_compliance_score: analysis.complianceScore / 100,
        compliance_issues: analysis.findings.map(finding => ({
          issue_type: finding.requirement.replace(/\s+/g, '_').toLowerCase(),
          description: finding.description,
          severity: finding.severity as 'critical' | 'major' | 'minor' | 'info',
          suggested_fix: `Address ${finding.section} requirements`
        }))
      },
      similar_sections: analysis.findings.map((finding, index) => ({
        section_text: finding.description,
        similarity_score: 0.85 + (index * 0.02), // Mock similarity scores
        source_metadata: {
          section: finding.section,
          document_title: `European Pharmacopoeia Section ${finding.section.split(' ')[1]}`,
          page_number: index + 1
        }
      })),
      search_metadata: {
        total_sections_found: analysis.findings.length,
        avg_similarity_score: 0.87,
        processing_time_ms: 1240
      }
    };
  }

  // Mock ground truth documents
  const mockGroundTruthDocuments: DocumentInfo[] = [
    {
      id: 'gt1',
      filename: 'European_Pharmacopoeia_2024.pdf',
      size: 12500000,
      uploadedAt: new Date('2024-01-01'),
      type: 'pdf',
      status: 'processed'
    },
    {
      id: 'gt2', 
      filename: 'FDA_Guidance_Analytical_Methods.pdf',
      size: 8750000,
      uploadedAt: new Date('2024-01-15'),
      type: 'pdf',
      status: 'processed'
    }
  ];
</script>

<svelte:head>
  <title>Sample Compliance Reports - GUARDIAN</title>
</svelte:head>

<svelte:window on:keydown={handleKeydown} />

{#if showAnalysis && selectedAnalysis}
  <!-- Show Analysis Results with new component -->
  <ProtocolAnalysisResults 
    analysis={convertToProtocolAnalysisResult(selectedAnalysis)}
    groundTruthDocuments={mockGroundTruthDocuments}
    on:backToReports={backToReports}
    on:generateReport={() => downloadReport(selectedAnalysis!)}
    on:clearAnalysis={backToReports}
  />
{:else}
  <!-- Show Reports Grid -->
  <div class="sample-reports-page">
    <!-- Hero Section -->
    <div class="hero">
      <div class="hero-content">
        <Icon name="file-text" size={48} color="var(--color-primary-600)" />
        <h1>Sample Compliance Reports</h1>
        <p>Example pharmaceutical compliance analyses to demonstrate GUARDIAN's capabilities</p>
        
        {#if !authenticated}
          <Card padding="md" glass>
            <div class="sample-notice">
              <Icon name="info" size={20} color="var(--color-primary-600)" />
              <div class="notice-content">
                <strong>Sample Reports</strong>
                <p>These are example compliance reports. Sign in to analyze your own documents.</p>
              </div>
              <Button variant="primary" onclick={signInToStart}>
                <Icon name="login" size={16} />
                Sign In to Start
              </Button>
            </div>
          </Card>
        {/if}
      </div>
    </div>

    <!-- Reports Grid -->
    <div class="reports-grid">
      {#each SAMPLE_REPORTS as analysis (analysis.id)}
        <Card hover>
          <button class="report-card" onclick={() => selectAnalysis(analysis)}>
            <div class="report-header">
              <div class="compliance-score {getComplianceScoreClass(analysis.complianceScore)}">
                <div class="score-value">{analysis.complianceScore}%</div>
                <div class="score-label">Compliance</div>
              </div>
              <Icon name="external-link" size={20} color="var(--color-gray-400)" />
            </div>

            <div class="report-content">
              <div class="analysis-meta">
                <div class="meta-item">
                  <Icon name="calendar" size={16} />
                  <span>{formatDate(analysis.createdAt)}</span>
                </div>
                <div class="meta-item">
                  <Icon name="search" size={16} />
                  <span>{analysis.findings.length} findings</span>
                </div>
                <div class="meta-item">
                  <Icon name="lightbulb" size={16} />
                  <span>{analysis.recommendations.length} recommendations</span>
                </div>
              </div>

              <div class="findings-preview">
                <div class="findings-stats">
                  <div class="stat compliant">
                    <span class="count">{analysis.findings?.filter(f => f.status === 'compliant').length || 0}</span>
                    <span class="label">Compliant</span>
                  </div>
                  <div class="stat partial">
                    <span class="count">{analysis.findings?.filter(f => f.status === 'partial').length || 0}</span>
                    <span class="label">Partial</span>
                  </div>
                  <div class="stat non-compliant">
                    <span class="count">{analysis.findings?.filter(f => f.status === 'non-compliant').length || 0}</span>
                    <span class="label">Issues</span>
                  </div>
                </div>
              </div>

              <div class="card-footer">
                <span class="view-label">Click to view detailed analysis</span>
                <Icon name="arrow-right" size={16} />
              </div>
            </div>
          </button>
        </Card>
      {/each}
    </div>
  </div>
{/if}


<style>
  .sample-reports-page {
    display: flex;
    flex-direction: column;
    gap: var(--space-8);
    max-width: var(--max-width-6xl);
    margin: 0 auto;
    padding: var(--space-6);
  }

  .hero {
    text-align: center;
    padding: var(--space-8) 0;
  }

  .hero-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-6);
    max-width: var(--max-width-2xl);
    margin: 0 auto;
  }

  .hero h1 {
    font-size: var(--font-size-4xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-text);
    margin: 0;
  }

  .hero p {
    font-size: var(--font-size-lg);
    color: var(--color-text-secondary);
    margin: 0;
    line-height: var(--line-height-relaxed);
  }

  .sample-notice {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    text-align: left;
  }

  .notice-content {
    flex: 1;
  }

  .notice-content strong {
    display: block;
    color: var(--color-primary-700);
    margin-bottom: var(--space-1);
    font-weight: var(--font-weight-semibold);
  }

  .notice-content p {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: var(--font-size-sm);
  }

  .reports-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
    gap: var(--space-6);
  }

  .report-card {
    display: flex;
    flex-direction: column;
    width: 100%;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    text-align: left;
  }

  .report-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--space-4);
  }

  .compliance-score {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: var(--space-4);
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    border: 2px solid;
    min-width: 120px;
  }

  .compliance-score.excellent {
    border-color: var(--color-success-400);
  }

  .compliance-score.excellent .score-value {
    color: var(--color-success-600);
  }

  .compliance-score.good {
    border-color: var(--color-success-400);
  }

  .compliance-score.good .score-value {
    color: var(--color-success-600);
  }

  .compliance-score.warning {
    border-color: var(--color-warning-400);
  }

  .compliance-score.warning .score-value {
    color: var(--color-warning-600);
  }

  .compliance-score.critical {
    border-color: var(--color-error-400);
  }

  .compliance-score.critical .score-value {
    color: var(--color-error-600);
  }

  .score-value {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
    line-height: 1;
  }

  .score-label {
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    text-transform: uppercase;
    margin-top: var(--space-1);
    opacity: 0.8;
  }

  .report-content {
    flex: 1;
  }

  .analysis-meta {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    margin-bottom: var(--space-4);
  }

  .meta-item {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    font-weight: var(--font-weight-medium);
  }

  .findings-preview {
    margin-bottom: var(--space-4);
  }

  .findings-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-3);
    padding: var(--space-4);
    background: var(--color-gray-50);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
  }

  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: var(--space-3);
    border-radius: var(--radius-md);
    background: white;
    border: 1px solid var(--color-border);
  }

  .stat.compliant {
    border-color: var(--color-success-200);
    background: var(--color-success-25);
  }

  .stat.partial {
    border-color: var(--color-warning-200);
    background: var(--color-warning-25);
  }

  .stat.non-compliant {
    border-color: var(--color-error-200);
    background: var(--color-error-25);
  }

  .stat .count {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-bold);
    line-height: 1;
  }

  .stat.compliant .count {
    color: var(--color-success-600);
  }

  .stat.partial .count {
    color: var(--color-warning-600);
  }

  .stat.non-compliant .count {
    color: var(--color-error-600);
  }

  .stat .label {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    font-weight: var(--font-weight-medium);
    margin-top: var(--space-1);
  }

  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: var(--space-3);
    border-top: 1px solid var(--color-border);
    color: var(--color-primary-600);
    font-weight: var(--font-weight-medium);
    font-size: var(--font-size-sm);
  }

  /* Modal/Overlay Styles - PRESERVED EXACTLY */
  .overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    animation: fadeIn 0.3s ease;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .overlay-content {
    background: var(--color-background);
    border-radius: 2rem;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
    width: 100%;
    height: 90vh;
    max-width: 1600px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }

  @keyframes slideUp {
    from {
      transform: translateY(50px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }

  .overlay-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2rem;
    background: linear-gradient(135deg, var(--color-primary-600), var(--color-primary-700));
    color: white;
    border-bottom: 3px solid var(--color-primary-400);
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 2rem;
  }

  .header-badge {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: rgba(255, 255, 255, 0.9);
    font-weight: 600;
    font-size: 0.875rem;
  }

  .compliance-score-hero {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 1.5rem;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .compliance-score-hero .score-value {
    font-size: 3rem;
    font-weight: 900;
    line-height: 1;
  }

  .compliance-score-hero .score-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.8);
    margin-top: 0.5rem;
  }

  .compliance-score-hero.excellent .score-value {
    color: #34d399;
  }

  .compliance-score-hero.good .score-value {
    color: #10b981;
  }

  .compliance-score-hero.warning .score-value {
    color: #fbbf24;
  }

  .compliance-score-hero.critical .score-value {
    color: #f87171;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }

  .close-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
    color: white;
  }

  .close-btn:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.05);
  }

  .analysis-layout {
    display: grid;
    grid-template-columns: 1fr 500px;
    gap: 0;
    flex: 1;
    overflow: hidden;
    background: var(--color-background);
  }

  .document-panel {
    display: flex;
    flex-direction: column;
    background: var(--color-surface);
    border-right: 2px solid var(--color-border);
  }

  .document-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 2rem;
    background: var(--color-background);
    border-bottom: 2px solid var(--color-border);
    position: sticky;
    top: 0;
    z-index: 10;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
  }

  .document-title {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .document-title h3 {
    font-size: 1.125rem;
    font-weight: 700;
    margin: 0;
    color: var(--color-text);
  }

  .document-meta {
    display: flex;
    align-items: center;
    gap: 1rem;
    font-size: 0.875rem;
  }

  .protocol-type {
    color: var(--color-success-700);
    font-weight: 500;
    background: var(--color-success-50);
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    border: 1px solid var(--color-success-200);
  }

  .analysis-date {
    color: var(--color-text-secondary);
    font-weight: 500;
  }

  .highlight-legend {
    display: flex;
    gap: 1.5rem;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .legend-color {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    border: none;
  }

  .document-content {
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
    font-size: 0.85rem;
    line-height: 1.7;
    color: var(--color-text);
    white-space: pre-wrap;
    height: 100%;
    overflow-y: auto;
    padding: 2rem;
    background: var(--color-surface);
    scroll-behavior: smooth;
  }

  /* Highlighting styles - PRESERVED EXACTLY */
  .document-content :global(.highlight-green) {
    background-color: var(--color-success-100);
    border-left: 4px solid var(--color-success-500);
    padding-left: 0.5rem;
    margin: 0.25rem 0;
    display: block;
  }

  .document-content :global(.highlight-yellow) {
    background-color: var(--color-warning-100);
    border-left: 4px solid var(--color-warning-500);
    padding-left: 0.5rem;
    margin: 0.25rem 0;
    display: block;
  }

  .document-content :global(.highlight-red) {
    background-color: var(--color-error-100);
    border-left: 4px solid var(--color-error-500);
    padding-left: 0.5rem;
    margin: 0.25rem 0;
    display: block;
  }

  .highlight-green {
    background-color: var(--color-success-200);
  }

  .highlight-yellow {
    background-color: var(--color-warning-200);
  }

  .highlight-red {
    background-color: var(--color-error-200);
  }

  .compliance-panel {
    display: flex;
    flex-direction: column;
    background: linear-gradient(135deg, var(--color-background) 0%, var(--color-surface) 100%);
    overflow-y: auto;
    height: 100%;
  }

  .analysis-content {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 2rem;
    gap: 2rem;
  }

  .analysis-overview-card {
    background: var(--color-surface);
    border-radius: 1rem;
    padding: 1.5rem;
    border: 1px solid var(--color-border);
  }

  .overview-stats {
    display: flex;
    justify-content: space-around;
    gap: 1rem;
  }

  .overview-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--color-text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
  }

  .findings-section, .recommendations-section {
    margin-bottom: 2rem;
  }

  .findings-section h4, .recommendations-section h4 {
    font-size: 1.125rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    color: var(--color-text);
  }

  .findings-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .finding-item {
    padding: 1.5rem;
    border-radius: 0.75rem;
    border: 1px solid var(--color-border);
    background: var(--color-gray-50);
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
  }

  .finding-item:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    border-color: var(--color-gray-300);
  }

  .finding-item.finding-compliant {
    background: var(--color-success-50);
    border-color: var(--color-success-200);
  }

  .finding-item.finding-partial {
    background: var(--color-warning-50);
    border-color: var(--color-warning-200);
  }

  .finding-item.finding-non-compliant {
    background: var(--color-error-50);
    border-color: var(--color-error-200);
  }

  .finding-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
  }

  .finding-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
  }

  .finding-status.info {
    color: var(--color-success-700);
  }

  .finding-status.minor {
    color: var(--color-blue-600);
  }

  .finding-status.major {
    color: var(--color-warning-700);
  }

  .finding-status.critical {
    color: var(--color-error-700);
  }

  .severity-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.025em;
  }

  .severity-badge.info {
    background: var(--color-success-100);
    color: var(--color-success-800);
  }

  .severity-badge.minor {
    background: var(--color-blue-100);
    color: var(--color-blue-800);
  }

  .severity-badge.major {
    background: var(--color-warning-100);
    color: var(--color-warning-800);
  }

  .severity-badge.critical {
    background: var(--color-error-100);
    color: var(--color-error-800);
  }

  .finding-content h5 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 0.5rem 0;
    color: var(--color-text);
  }

  .finding-content .requirement {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-primary-600);
    margin-bottom: 0.75rem;
  }

  .finding-content .description {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    line-height: 1.5;
    margin: 0 0 1rem 0;
  }

  .goto-section-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-top: 0.5rem;
  }

  .goto-section-btn:hover {
    background: #1e40af;
    transform: translateY(-1px);
  }

  .recommendations-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .recommendation-item {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    background: var(--color-blue-50);
    border: 1px solid var(--color-blue-200);
    border-radius: 0.5rem;
  }

  .recommendation-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    background: var(--color-primary-500);
    color: white;
    border-radius: 50%;
    font-weight: 600;
    font-size: 0.875rem;
    flex-shrink: 0;
  }

  .recommendation-text {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    line-height: 1.5;
  }

  /* Responsive Design */
  @media (max-width: 1400px) {
    .reports-grid {
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    }
  }

  @media (max-width: 1200px) {
    .analysis-layout {
      grid-template-columns: 1fr;
      height: auto;
    }

    .compliance-panel {
      order: -1;
      max-height: 50vh;
    }

    .document-content {
      max-height: 40vh;
    }
  }

  @media (max-width: 768px) {
    .sample-reports-page {
      padding: var(--space-4);
    }

    .hero h1 {
      font-size: var(--font-size-2xl);
    }

    .reports-grid {
      grid-template-columns: 1fr;
      gap: var(--space-4);
    }

    .report-header {
      flex-direction: column;
      align-items: center;
      text-align: center;
    }

    .overlay {
      padding: 1rem;
    }

    .overlay-content {
      height: 95vh;
    }

    .document-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .highlight-legend {
      flex-wrap: wrap;
    }

    .sample-notice {
      flex-direction: column;
      text-align: center;
      gap: var(--space-3);
    }

    .overlay-header {
      flex-direction: column;
      gap: 1rem;
      text-align: center;
    }

    .header-left {
      flex-direction: column;
      gap: 1rem;
    }
  }
</style>