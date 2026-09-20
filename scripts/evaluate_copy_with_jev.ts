import fs from 'node:fs';
import path from 'node:path';
import { experimental_evaluate } from 'ai';

interface EmailCopySample {
  segment: string;
  tier: 'person' | 'company';
  signalType: string;
  email1: { subject: string; body: string };
  email2: { subject: string; body: string };
  email3: { subject: string; body: string };
}

const SAMPLES: EmailCopySample[] = [
  {
    segment: 'home_design',
    tier: 'company',
    signalType: 'social_video',
    email1: {
      subject: 'boca raton interior designer',
      body: `Hi,\n\nYou are set up on Instagram, yet the website carries no video. For interior designer teams, that is often the gap between a visit and an inquiry.\n\nWe finish site and portfolio footage you already have: cinematic pacing, color grade, and hook-led reels cut from one master.\n\nWant a sample edit matched to your style of work?`
    },
    email2: {
      subject: 'second angle on boca raton interior designer',
      body: `Hi,\n\nHigh-ticket clients often judge the build quality by the reel quality before they ever call.\n\nWe turn raw project footage into reels that look as considered as the finished build.\n\nUseful if I send a short example matched to your niche?`
    },
    email3: {
      subject: 'post-build video workflow',
      body: `Hi,\n\nClosing the loop here. Publishing finished video consistently is nearly always a bandwidth problem, not a content problem.\n\nIf it's bandwidth, that's exactly the gap we fill: post-production only, on your media.\n\nWant one sample cut so you can judge the finish directly?`
    }
  },
  {
    segment: 'creative_marketing',
    tier: 'person',
    signalType: 'linkedin_posts',
    email1: {
      subject: 'austin ad agency',
      body: `Hi Sarah,\n\nSaw your recent LinkedIn post ("building full-funnel retention for Q4"), so video is clearly already part of how you show up. The lever from here is usually the finish, not more posting.\n\nWe plug in as a white-label finishing bench: retention edits, motion graphics, and hook variants on your clients' footage, delivered under your name.\n\nOpen to a short sample reel showing how we cut agency footage?`
    },
    email2: {
      subject: 'overflow edit bench',
      body: `Hi Sarah,\n\nFrom one client master we typically deliver ten platform-native shorts plus twenty hook variations for paid testing.\n\nAgencies use us when edit queues back up but hiring another full-time editor does not make sense.\n\nWorth sending a 60-second walkthrough of our agency deliverables?`
    },
    email3: {
      subject: 'wrapping up on austin ad agency',
      body: `Hi Sarah,\n\nLast note from my end. Usually when agencies pass on this, it's either because edit capacity is totally fine in-house, or the timing is off.\n\nIf you ever need an overflow bench on short notice, we're here.\n\nShould I check back next quarter instead?`
    }
  },
  {
    segment: 'real_estate',
    tier: 'company',
    signalType: 'weak',
    email1: {
      subject: 'miami commercial real estate',
      body: `Hi,\n\nMost commercial real estate teams in Miami sit on usable footage already: walkthroughs, events, phone clips that never become finished video.\n\nWe finish walkthrough and event footage you already shoot: pacing, captions, and short reels cut from one master. No new shoot needed.\n\nCan I send a sample reel matched to your listing types?`
    },
    email2: {
      subject: 'listing reels from phone footage',
      body: `Hi,\n\nListings with paced, hook-led reels tend to earn attention long before the floor plan gets read.\n\nOne walkthrough typically becomes a hero tour plus a set of 15-30 second reels sized for Instagram and YouTube.\n\nWorth a quick look at an example?`
    },
    email3: {
      subject: 'listing video turnaround',
      body: `Hi,\n\nClosing the loop. If video isn't on the radar for your team this quarter, no worries at all.\n\nWe do post-production only on existing media when teams need finished assets without running a new shoot.\n\nWant me to reach back out in a few months?`
    }
  }
];

const QUESTIONS = {
  hookClarityAndRelevance: {
    type: 'score' as const,
    instructions: 'Rate the opener hook: does it feel personalized, natural, and relevant to the prospect?',
    criteria: [
      'Poor: Obvious generic template, spammy, or irrelevant',
      'Good: Clear observation, relevant to the industry, reasonable bridge',
      'Excellent: Highly authentic, specific verifiable signal, zero fluff'
    ]
  },
  valueClarity: {
    type: 'score' as const,
    instructions: 'How clearly does the copy communicate what the sender does (post-production on existing footage) and the tangible benefit?',
    criteria: [
      'Poor: Vague offer, confusing deliverables, or over-hyped buzzwords',
      'Good: Understandable offer and deliverable scope',
      'Excellent: Crystal clear scope (no shoots, post-production only, turnkey deliverables), immediate value comprehension'
    ]
  },
  ctaFriction: {
    type: 'choice' as const,
    instructions: 'How is the Call To Action (CTA) calibrated?',
    criteria: {
      low_friction_sample: 'Low friction: asks to send a sample/example or check back later (appropriate for cold outreach)',
      moderate_friction: 'Moderate: asks for feedback or short thoughts',
      high_friction_meeting: 'High friction: asks for a phone call, demo, or meeting prematurely'
    }
  },
  soundsLikeAITell: {
    type: 'boolean' as const,
    instructions: 'Does this email contain obvious AI writing hallmarks (em dashes, overly symmetrical phrasing, formulaic transitions)?'
  },
  replyPotential: {
    type: 'choice' as const,
    instructions: 'Estimate the reply potential of this sequence for B2B cold outreach',
    criteria: {
      high: 'High: Conversational, respectful, clear hook, low-friction ask',
      average: 'Average: Standard cold email, will get typical benchmark response',
      low: 'Low: Likely to be ignored, deleted, or marked spam'
    }
  },
  keyImprovementArea: {
    type: 'choice' as const,
    instructions: 'What is the highest-leverage improvement to raise conversion further?',
    criteria: {
      more_concrete_metrics: 'Add specific proof points or turnaround time (e.g. 48-hour turn, exact asset count)',
      sharpen_first_line: 'Make the first sentence even more direct and conversational',
      tighter_segment_pain: 'Focus even more deeply on the specific operational pain of that niche',
      keep_as_is: 'Copy is already dialed in; no major edits recommended'
    }
  }
};

async function evaluateSequence(sample: EmailCopySample) {
  console.log(`\n======================================================`);
  console.log(`Evaluating Sequence: [${sample.segment.toUpperCase()}] (Tier: ${sample.tier}, Signal: ${sample.signalType})`);
  console.log(`======================================================`);

  const state = `
SEGMENT: ${sample.segment}
OUTREACH TIER: ${sample.tier}
SIGNAL SOURCE: ${sample.signalType}

EMAIL 1:
Subject: ${sample.email1.subject}
Body:
${sample.email1.body}

EMAIL 2:
Subject: ${sample.email2.subject}
Body:
${sample.email2.body}

EMAIL 3:
Subject: ${sample.email3.subject}
Body:
${sample.email3.body}
`;

  const result = await experimental_evaluate({
    model: 'typesafe-ai/jev',
    state,
    questions: QUESTIONS
  });

  const a = result.answers as any;

  console.log(`- Hook Relevance:      Score ${a.hookClarityAndRelevance?.score?.toFixed(2)} / 2.0 (prob: ${JSON.stringify(a.hookClarityAndRelevance?.probabilities)})`);
  console.log(`- Value Clarity:       Score ${a.valueClarity?.score?.toFixed(2)} / 2.0 (prob: ${JSON.stringify(a.valueClarity?.probabilities)})`);
  console.log(`- CTA Friction:        ${a.ctaFriction?.choice} (prob: ${JSON.stringify(a.ctaFriction?.probabilities)})`);
  console.log(`- AI Tells Detected:   ${(a.soundsLikeAITell?.probability * 100).toFixed(1)}% probability`);
  console.log(`- Reply Potential:     ${a.replyPotential?.choice.toUpperCase()} (prob: ${JSON.stringify(a.replyPotential?.probabilities)})`);
  console.log(`- Top Improvement:     ${a.keyImprovementArea?.choice} (prob: ${JSON.stringify(a.keyImprovementArea?.probabilities)})`);

  return { sample, answers: a };
}

async function main() {
  console.log('Asking TypeSafe Jev to evaluate email copywriting quality across segments...\n');
  const results = [];
  for (const s of SAMPLES) {
    const res = await evaluateSequence(s);
    results.push(res);
  }

  console.log('\n\n======================================================');
  console.log('JEV COPYWRITING QUALITY EVALUATION SUMMARY');
  console.log('======================================================');
  for (const r of results) {
    console.log(`* [${r.sample.segment}] (${r.sample.signalType}) -> Reply: ${r.answers.replyPotential?.choice.toUpperCase()} | Hook: ${r.answers.hookClarityAndRelevance?.score?.toFixed(2)}/2.0 | AI Tell: ${(r.answers.soundsLikeAITell?.probability * 100).toFixed(0)}% | Lever: ${r.answers.keyImprovementArea?.choice}`);
  }
}

main().catch(console.error);
