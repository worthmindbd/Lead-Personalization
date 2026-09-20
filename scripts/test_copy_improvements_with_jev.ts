import { experimental_evaluate } from 'ai';

const COMPARISONS = [
  {
    name: 'Home Design (social_video signal)',
    original: `Hi,

You are set up on Instagram, yet the website carries no video. For interior designer teams, that is often the gap between a visit and an inquiry.

We finish site and portfolio footage you already have: cinematic pacing, color grade, and hook-led reels cut from one master.

Want a sample edit matched to your style of work?`,
    improved: `Hi,

Noticed your Instagram link on the site, but no video on the homepage itself. For high-end design projects, clients usually want to see the space in motion before booking an intro consult.

We turn existing phone walkthroughs and camera rolls into finished portfolio reels (DaVinci color grade, clean pacing, and 9:16 vertical cuts delivered in 48-72 hours). No new shoot required.

Can I send over a 30-second sample cut matched to your aesthetic?`
  },
  {
    name: 'Creative Agency (linkedin_posts signal)',
    original: `Hi Sarah,

Saw your recent LinkedIn post ("building full-funnel retention for Q4"), so video is clearly already part of how you show up. The lever from here is usually the finish, not more posting.

We plug in as a white-label finishing bench: retention edits, motion graphics, and hook variants on your clients' footage, delivered under your name.

Open to a short sample reel showing how we cut agency footage?`,
    improved: `Hi Sarah,

Saw your LinkedIn post on Q4 retention strategies. If video client demands are stacking up for Q4, we act as a white-label overflow edit bench for agencies.

You drop raw client footage into a shared drive; we deliver retention cuts, motion graphics, and 10+ hook variants per master within 3-4 business days, ready for client review under your brand.

Open to seeing a 45-second agency sample package?`
  }
];

async function compareCopy() {
  console.log('Testing Original vs Jev-Optimized Copy Head-to-Head with Jev...\n');

  for (const comp of COMPARISONS) {
    console.log(`======================================================`);
    console.log(`Comparison: ${comp.name}`);
    console.log(`======================================================`);

    const evalOriginal = await experimental_evaluate({
      model: 'typesafe-ai/jev',
      state: `VERSION: ORIGINAL\n\n${comp.original}`,
      questions: {
        effectiveness: {
          type: 'score',
          instructions: 'Rate cold email effectiveness (human tone, concrete offer, reply likelihood)',
          criteria: ['Weak', 'Average', 'Highly Effective']
        },
        hasConcreteMetrics: {
          type: 'boolean',
          instructions: 'Does this email give concrete turnaround times, deliverables, or operational specifics?'
        },
        humanTone: {
          type: 'score',
          instructions: 'Rate how natural and human (vs AI-generated) the copy sounds',
          criteria: ['Formulaic/AI-sounding', 'Decent', 'Completely natural peer-to-peer']
        }
      }
    });

    const evalImproved = await experimental_evaluate({
      model: 'typesafe-ai/jev',
      state: `VERSION: IMPROVED\n\n${comp.improved}`,
      questions: {
        effectiveness: {
          type: 'score',
          instructions: 'Rate cold email effectiveness (human tone, concrete offer, reply likelihood)',
          criteria: ['Weak', 'Average', 'Highly Effective']
        },
        hasConcreteMetrics: {
          type: 'boolean',
          instructions: 'Does this email give concrete turnaround times, deliverables, or operational specifics?'
        },
        humanTone: {
          type: 'score',
          instructions: 'Rate how natural and human (vs AI-generated) the copy sounds',
          criteria: ['Formulaic/AI-sounding', 'Decent', 'Completely natural peer-to-peer']
        }
      }
    });

    const origAns = evalOriginal.answers as any;
    const impAns = evalImproved.answers as any;

    console.log(`ORIGINAL:`);
    console.log(`  - Overall Effectiveness: ${origAns.effectiveness?.score?.toFixed(2)} / 2.0`);
    console.log(`  - Has Concrete Metrics:   ${(origAns.hasConcreteMetrics?.probability * 100).toFixed(0)}%`);
    console.log(`  - Human Peer Tone:       ${origAns.humanTone?.score?.toFixed(2)} / 2.0\n`);

    console.log(`IMPROVED:`);
    console.log(`  - Overall Effectiveness: ${impAns.effectiveness?.score?.toFixed(2)} / 2.0`);
    console.log(`  - Has Concrete Metrics:   ${(impAns.hasConcreteMetrics?.probability * 100).toFixed(0)}%`);
    console.log(`  - Human Peer Tone:       ${impAns.humanTone?.score?.toFixed(2)} / 2.0\n`);

    const diff = impAns.effectiveness?.score - origAns.effectiveness?.score;
    console.log(`IMPROVEMENT DELTA: ${diff >= 0 ? '+' : ''}${diff.toFixed(2)} points in effectiveness!\n`);
  }
}

compareCopy().catch(console.error);
