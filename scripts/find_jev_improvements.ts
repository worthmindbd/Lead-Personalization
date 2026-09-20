import fs from 'node:fs';
import path from 'node:path';
import { experimental_evaluate } from 'ai';

interface InspectionItem {
  file: string;
  focus: string;
}

const ITEMS: InspectionItem[] = [
  // Group 1: Core Primitives
  { file: 'lead_personalization/config.py', focus: 'Missing env validation, type safety, default value edge cases' },
  { file: 'lead_personalization/fsutil.py', focus: 'Flock unlock failure safety, tmp file cleanup, error handling' },
  { file: 'lead_personalization/sanitize.py', focus: 'Encoding edge cases, unicode handling, truncation' },
  { file: 'lead_personalization/qa.py', focus: 'Rule edge cases, missing assertions, regex safety' },
  
  // Group 2: Research & Headless
  { file: 'lead_personalization/research.py', focus: 'HTTP request timeouts, SSRF/bad URL filtering, error handling' },
  { file: 'lead_personalization/render_page.js', focus: 'Process argument safety, unhandled rejections, timeout leak' },
  { file: 'lead_personalization/linkedin.py', focus: 'Cache file lock timeout, Apify error handling, token rotation' },

  // Group 4: Batch Orchestration
  { file: 'scripts/personalization/create_batch_manifest.py', focus: 'Manifest schema validation, corrupted input handling' },
  { file: 'scripts/personalization/process_batch.py', focus: 'Crash recovery, exception propagation, signal handling' },
  { file: 'scripts/personalization/merge_enriched.py', focus: 'Duplicate header handling, atomic output writing, data loss' }
];

async function inspectItem(item: InspectionItem) {
  const fullPath = path.resolve(process.cwd(), item.file);
  const code = fs.readFileSync(fullPath, 'utf8');

  const result = await experimental_evaluate({
    model: 'typesafe-ai/jev',
    state: `FILE: ${item.file}\nFOCUS: ${item.focus}\n\n${code}`,
    questions: {
      hasImprovementOpportunity: {
        type: 'boolean',
        instructions: 'Can this file be significantly improved in error handling, security, or robustness?'
      },
      recommendedAction: {
        type: 'choice',
        instructions: 'What is the top recommended improvement for this code?',
        criteria: {
          tighten_error_handling: 'Add defensive try/except blocks, validate inputs, or prevent unhandled exceptions',
          strengthen_security: 'Sanitize URLs, prevent file overwrite/injection, or guard sensitive data',
          clean_code_and_types: 'Simplify complex logic, remove redundant branches, or improve typing',
          already_clean: 'Code is already clean and robust; no major changes needed'
        }
      },
      qualityScore: {
        type: 'score',
        instructions: 'Rate the overall quality',
        criteria: ['Needs Work', 'Good', 'Excellent']
      }
    }
  });

  return {
    file: item.file,
    answers: result.answers as any
  };
}

async function main() {
  console.log('Inspecting candidate files for improvements with Jev...\n');
  for (const item of ITEMS) {
    const res = await inspectItem(item);
    const ans = res.answers;
    console.log(`[${res.file}]`);
    console.log(`  Opportunity: ${(ans.hasImprovementOpportunity?.probability * 100).toFixed(1)}% | Quality: ${ans.qualityScore?.score?.toFixed(2)}/2.0`);
    console.log(`  Top Action:  ${ans.recommendedAction?.choice} (prob: ${JSON.stringify(ans.recommendedAction?.probabilities)})\n`);
  }
}

main().catch(console.error);
