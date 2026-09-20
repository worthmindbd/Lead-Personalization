import fs from 'node:fs';
import path from 'node:path';
import { experimental_evaluate } from 'ai';

interface FileTarget {
  path: string;
  focus: string;
}

const TARGETS: FileTarget[] = [
  {
    path: 'lead_personalization/renderers.py',
    focus: 'Subprocess security, timeout handling, and shell injection defense'
  },
  {
    path: 'lead_personalization/fsutil.py',
    focus: 'Atomic file writes, file locking, and crash safety'
  },
  {
    path: 'scripts/personalization/manifest_lock.py',
    focus: 'Concurrency, race conditions, and stale lock recovery'
  },
  {
    path: 'lead_personalization/naming.py',
    focus: 'Regex sanitization, edge cases in company/person name normalization'
  }
];

async function reviewTarget(target: FileTarget) {
  const fullPath = path.resolve(process.cwd(), target.path);
  const code = fs.readFileSync(fullPath, 'utf8');

  const result = await experimental_evaluate({
    model: 'typesafe-ai/jev',
    state: `FOCUS: ${target.focus}\n\n${code}`,
    questions: {
      actionNeeded: {
        type: 'choice',
        instructions: 'What immediate engineering action is needed for this file?',
        criteria: {
          no_action_needed: 'Code is robust and safe; no changes required',
          improve_error_handling: 'Needs tighter exception handling, timeout cleanup, or fallback logic',
          strengthen_security: 'Needs stricter sanitization, argument escaping, or permission tightening',
          simplify_logic: 'Logic is overly complex and can be streamlined'
        }
      },
      hasVulnerability: {
        type: 'boolean',
        instructions: 'Does this code contain a vulnerability (e.g. command injection, race condition, data corruption)?'
      },
      qualityScore: {
        type: 'score',
        instructions: 'Rate the technical implementation quality',
        criteria: [
          'Poor: Needs immediate attention',
          'Good: Production ready with minor room for improvement',
          'Excellent: Exemplary implementation'
        ]
      }
    }
  });

  return {
    path: target.path,
    focus: target.focus,
    answers: result.answers as any
  };
}

async function main() {
  console.log('Running Focused Jev Reviews on Key High-Impact Modules...\n');
  const results = [];
  for (const t of TARGETS) {
    const res = await reviewTarget(t);
    results.push(res);
    console.log(`[${res.path}] (${res.focus})`);
    console.log(`  Action: ${res.answers.actionNeeded?.choice} (prob: ${JSON.stringify(res.answers.actionNeeded?.probabilities)})`);
    console.log(`  Vulnerability Probability: ${(res.answers.hasVulnerability?.probability * 100).toFixed(1)}%`);
    console.log(`  Quality Score: ${res.answers.qualityScore?.score?.toFixed(2)} / 2.0\n`);
  }
}

main().catch(console.error);
