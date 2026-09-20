import { generateText, experimental_evaluate } from 'ai';

/**
 * TypeSafe Jev via Vercel AI Gateway Demo
 *
 * Official Docs: https://docs.typesafe.ai/
 * Jev is a "System One" decision model, not a generative language model.
 * - generateText() expects a generative language model (returns text).
 * - Jev does not generate text/prose; it evaluates state against typed questions (boolean, choice, score).
 */

async function testGenerateText() {
  console.log('--- 1. Testing generateText with typesafe-ai/jev ---');
  try {
    const result = await generateText({
      model: 'typesafe-ai/jev',
      prompt: 'Review this code: const x = 1;',
    });
    console.log('generateText result:', result.text);
    return true;
  } catch (error: any) {
    console.log('generateText failed as expected:');
    console.log(`  Error: ${error.message || error}`);
    console.log('  Reason: Jev is a System One evaluation model, not a text generation LLM.\n');
    return false;
  }
}

async function runCodeReviewEvaluation(codeToReview: string) {
  console.log('--- 2. Performing Code Review using experimental_evaluate with typesafe-ai/jev ---');
  console.log('Code under review:\n', codeToReview.trim(), '\n');

  const result = await experimental_evaluate({
    model: 'typesafe-ai/jev',
    state: codeToReview,
    questions: {
      hasCriticalBug: {
        type: 'boolean',
        instructions: 'Does this code have syntax errors, unhandled exceptions, or critical runtime bugs?'
      },
      hasSecurityIssue: {
        type: 'boolean',
        instructions: 'Does this code expose secrets, allow injection, or have security vulnerabilities?'
      },
      qualityScore: {
        type: 'score',
        instructions: 'Rate the code quality and readability on a 3-tier scale',
        criteria: [
          'Poor: Buggy, unreadable, or missing essentials',
          'Acceptable: Functional and standard',
          'Excellent: Clean, idiomatic, and robust'
        ]
      },
      decision: {
        type: 'choice',
        instructions: 'What code review action should be taken?',
        criteria: {
          approve: 'Code is clean and safe to merge',
          request_changes: 'Code has bugs or style issues that must be fixed',
          flag_security: 'Code has potential security or secret leakage concerns'
        }
      }
    }
  });

  console.log('Jev Evaluation Results:');
  console.log(JSON.stringify(result.answers, null, 2));

  // Acting on Jev's decisions programmatically:
  console.log('\n--- 3. Programmatic Decision Branching ---');
  const answers = result.answers as any;

  if (answers.hasSecurityIssue?.probability > 0.5 || answers.decision?.choice === 'flag_security') {
    console.log('ACTION: BLOCKED - Security review required!');
  } else if (answers.hasCriticalBug?.probability > 0.5 || answers.decision?.choice === 'request_changes') {
    console.log('ACTION: CHANGES REQUESTED - Bugs detected.');
  } else {
    console.log('ACTION: APPROVED - Code passed System One evaluation.');
  }

  return result;
}

async function main() {
  await testGenerateText();

  const sampleCode = `
function calculateDiscount(price: number, discountPercent: number): number {
  if (price < 0 || discountPercent < 0 || discountPercent > 100) {
    throw new Error('Invalid price or discount percentage');
  }
  return price * (1 - discountPercent / 100);
}
`;

  await runCodeReviewEvaluation(sampleCode);
}

main().catch(console.error);
