import fs from 'node:fs';
import path from 'node:path';
import { experimental_evaluate } from 'ai';

interface ModuleGroup {
  name: string;
  description: string;
  files: string[];
}

const MODULE_GROUPS: ModuleGroup[] = [
  {
    name: '1. Core Primitives & Sanitization',
    description: 'Configuration, file utilities, naming sanitization, QA checks, and text normalization.',
    files: [
      'lead_personalization/config.py',
      'lead_personalization/naming.py',
      'lead_personalization/fsutil.py',
      'lead_personalization/sanitize.py',
      'lead_personalization/qa.py'
    ]
  },
  {
    name: '2. Research & Headless Fallbacks',
    description: 'Website scraping, DOM signal extraction, headless Chromium renderer, and LinkedIn scraper.',
    files: [
      'lead_personalization/research.py',
      'lead_personalization/renderers.py',
      'lead_personalization/render_page.js',
      'lead_personalization/linkedin.py'
    ]
  },
  {
    name: '3. Deterministic Copy Engine',
    description: 'Offer pack loader, variant selection, subject generator, segment classification, and row pipeline.',
    files: [
      'lead_personalization/offer_pack.py',
      'lead_personalization/copywriter.py',
      'lead_personalization/subjects.py',
      'lead_personalization/segments.py',
      'lead_personalization/pipeline.py'
    ]
  },
  {
    name: '4. Batch Orchestration & Enriched Merges',
    description: 'Batch manifests, locking, parallel workers, normalization, and enriched lead merging.',
    files: [
      'scripts/personalization/artifacts.py',
      'scripts/personalization/normalize_leads.py',
      'scripts/personalization/create_batch_manifest.py',
      'scripts/personalization/manifest_lock.py',
      'scripts/personalization/process_batch.py',
      'scripts/personalization/run_batches.py',
      'scripts/personalization/merge_enriched.py'
    ]
  },
  {
    name: '5. Pipeline Orchestration & Cloud Services',
    description: 'Drive orchestrator, Reoon email verification, Google Sheets reporting, and sync.',
    files: [
      'scripts/pipeline/run_pipeline.py',
      'scripts/pipeline/report.py',
      'scripts/pipeline/sheets_sync.py',
      'scripts/verify_emails_reoon.py'
    ]
  }
];

function loadModuleContent(files: string[]): string {
  const parts: string[] = [];
  for (const relPath of files) {
    const fullPath = path.resolve(process.cwd(), relPath);
    if (fs.existsSync(fullPath)) {
      const content = fs.readFileSync(fullPath, 'utf8');
      parts.push(`=== FILE: ${relPath} ===\n${content}\n`);
    } else {
      parts.push(`=== FILE: ${relPath} (NOT FOUND) ===\n`);
    }
  }
  return parts.join('\n');
}

const QUESTIONS = {
  maintainability: {
    type: 'score' as const,
    instructions: 'Rate the maintainability, modularity, and code structure of this code.',
    criteria: [
      'Poor: Hard to follow, monolithic, high coupling, or poor naming',
      'Acceptable: Functional, understandable, standard idioms',
      'Excellent: Clean abstractions, highly modular, clear boundaries and types'
    ]
  },
  errorHandling: {
    type: 'score' as const,
    instructions: 'Rate the robustness of error handling and failure recovery.',
    criteria: [
      'Poor: Missing error handling, unhandled edge cases, brittle assumptions',
      'Acceptable: Handles expected errors reasonably with logging or fallback',
      'Excellent: Defensive design, graceful degradation, comprehensive recovery'
    ]
  },
  hasSecurityOrDataRisk: {
    type: 'boolean' as const,
    instructions: 'Does this code expose secrets, allow command/code injection, or carry data loss risks?'
  },
  hasDeadOrRedundantCode: {
    type: 'boolean' as const,
    instructions: 'Does this code contain noticeable dead code, duplicated logic, or unused branches?'
  },
  reviewDecision: {
    type: 'choice' as const,
    instructions: 'What code review decision should be made for this module?',
    criteria: {
      approve: 'High code quality; clean, robust, and ready for production',
      minor_refactor: 'Good quality; minor cleanup, comments, or typing improvements suggested',
      needs_rework: 'Significant issues present; needs refactoring or bug fixes'
    }
  }
};

async function evaluateModule(group: ModuleGroup) {
  console.log(`\n======================================================`);
  console.log(`Evaluating: ${group.name}`);
  console.log(`Description: ${group.description}`);
  console.log(`Files: ${group.files.join(', ')}`);
  console.log(`======================================================`);

  const state = loadModuleContent(group.files);

  // If state is very large (> 25k tokens / ~100k chars), sample representative sections or evaluate cleanly
  const truncatedState = state.length > 120000 
    ? state.slice(0, 120000) + '\n\n[... truncated for context limits ...]' 
    : state;

  const result = await experimental_evaluate({
    model: 'typesafe-ai/jev',
    state: truncatedState,
    questions: QUESTIONS
  });

  const answers = result.answers as any;

  console.log('Jev Evaluation:');
  console.log(`  - Maintainability: Score ${answers.maintainability?.score?.toFixed(2)} / 2.00 (prob: ${JSON.stringify(answers.maintainability?.probabilities)})`);
  console.log(`  - Error Handling:  Score ${answers.errorHandling?.score?.toFixed(2)} / 2.00 (prob: ${JSON.stringify(answers.errorHandling?.probabilities)})`);
  console.log(`  - Security / Risk: Probability ${(answers.hasSecurityOrDataRisk?.probability * 100).toFixed(1)}%`);
  console.log(`  - Dead/Redundant:  Probability ${(answers.hasDeadOrRedundantCode?.probability * 100).toFixed(1)}%`);
  console.log(`  - Decision:        ${answers.reviewDecision?.choice.toUpperCase()} (probabilities: ${JSON.stringify(answers.reviewDecision?.probabilities)})`);

  return {
    group,
    answers
  };
}

async function runFullProjectReview() {
  console.log('Starting TypeSafe Jev Code Quality Review across the full project...');
  const results = [];

  for (const group of MODULE_GROUPS) {
    try {
      const res = await evaluateModule(group);
      results.push(res);
    } catch (err: any) {
      console.error(`Error evaluating ${group.name}:`, err.message || err);
    }
  }

  console.log('\n\n======================================================');
  console.log('SUMMARY OF JEV CODE REVIEW DECISIONS');
  console.log('======================================================');
  for (const r of results) {
    const d = r.answers.reviewDecision?.choice;
    const maint = r.answers.maintainability?.score?.toFixed(2);
    const err = r.answers.errorHandling?.score?.toFixed(2);
    const sec = (r.answers.hasSecurityOrDataRisk?.probability * 100).toFixed(1);
    console.log(`- ${r.group.name}:`);
    console.log(`    Decision: ${d.toUpperCase()} | Maintainability: ${maint}/2.0 | Error Handling: ${err}/2.0 | Security Risk: ${sec}%`);
  }
}

runFullProjectReview().catch(console.error);
