import { experimental_evaluate } from 'ai';

interface Sample {
  id: string;
  segment: string;
  tier: 'person' | 'company';
  evidence: string;
  variant: string;
  email1: { subject: string; body: string };
  email2: { subject: string; body: string };
  email3: { subject: string; body: string };
}

const SAMPLES: Sample[] = [
  {
    id: "home_design_person_site_video",
    segment: "home_design",
    tier: "person",
    evidence: "site_video",
    variant: "site_video.o1s0a0cl1su0c120",
    email1: {
      subject: "portfolio showcase",
      body: "Hi Alex,\n\nYour site embeds video, and that is rarer than it should be for interior design teams in Austin. What separates a view from an inquiry is almost always the finishing, not the footage.\n\nWe finish site and portfolio footage you already have: cinematic pacing, color grade, and hook-led reels cut from one master.\n\nWorth a short sample cut from your existing footage?"
    },
    email2: {
      subject: "reels vs long walkthroughs",
      body: "Hi Alex,\n\nOne site capture usually becomes a hero reveal plus platform-native reels for the same project.\n\nWe turn phone walkthroughs and raw site clips into color-graded portfolio reels delivered in 48-72 hours, without pulling your team into an editor.\n\nUseful if I send a short example matched to your niche?"
    },
    email3: {
      subject: "project video backlog",
      body: "Hi Alex,\n\nClosing the loop here. Publishing finished video consistently is nearly always a bandwidth problem, not a content problem.\n\nIf it's backlog, we run as a quiet post-production bench on footage you supply.\n\nWhen footage gets shot on your side, who finishes it, or does it wait?"
    }
  },
  {
    id: "creative_marketing_person_linkedin",
    segment: "creative_marketing",
    tier: "person",
    evidence: "linkedin_posts",
    variant: "linkedin_posts.o1s1a1cl0su0c012",
    email1: {
      subject: "scaling paid retention in q4",
      body: "Hi Sarah,\n\nYour recent LinkedIn post (\"scaling paid retention in Q4\") caught my eye. Teams posting that consistently usually gain the most from sharper finishing on the video side.\n\nWe handle overflow post-production in 48-72 hours: you drop raw client footage into a shared folder, and we deliver final branded cuts ready for client review.\n\nInterested in a sample edit from one clip you already have?"
    },
    email2: {
      subject: "hook variants for ads",
      body: "Hi Sarah,\n\nAgencies use us to turn one master edit into a full short-form package: paced cuts, captions, and test-ready hooks.\n\nWe plug in as a white-label finishing bench: retention edits, motion graphics, and hook variants on your clients' footage, delivered under your name.\n\nOpen to one before/after example?"
    },
    email3: {
      subject: "overflow edit workflow",
      body: "Hi Sarah,\n\nLast note from me: most teams we work with didn't lack footage, they lacked finishing time.\n\nIf it's backlog, we run as a quiet post-production bench on footage you supply.\n\nWorth keeping in mind for when queues spike, or is capacity completely handled?"
    }
  },
  {
    id: "real_estate_company_social_video",
    segment: "real_estate",
    tier: "company",
    evidence: "social_video",
    variant: "social_video.o1s1a1cl1su0c220",
    email1: {
      subject: "active instagram video tour",
      body: "Hi,\n\nYou are set up on Instagram, yet the website carries no video. For commercial real estate teams, that is often the gap between a visit and an inquiry.\n\nWe turn raw property walkthroughs into finished 9:16 reels and hero tours in 48 hours, formatted for Instagram, YouTube, and MLS listings.\n\nWant a sample edit matched to your style of work?"
    },
    email2: {
      subject: "listing clip pacing",
      body: "Hi,\n\nListings with paced, hook-led reels tend to earn attention long before the floor plan gets read.\n\nWe finish walkthrough and event footage you already shoot: pacing, captions, and short reels cut from one master. No new shoot needed.\n\nUseful if I send a short example matched to your niche?"
    },
    email3: {
      subject: "walkthrough backlog",
      body: "Hi,\n\nClosing the loop here. Publishing finished video consistently is nearly always a bandwidth problem, not a content problem.\n\nIf it's backlog, we run as a quiet post-production bench on footage you supply.\n\nWhen footage gets shot on your side, who finishes it, or does it wait?"
    }
  },
  {
    id: "software_tech_person_positioning",
    segment: "software_tech",
    tier: "person",
    evidence: "positioning",
    variant: "positioning.o1s0a0cl1su0c112",
    email1: {
      subject: "fastest ci/cd observability",
      body: "Hi Marcus,\n\n\"fastest CI/CD observability for Kubernetes\" is a strong promise on your homepage. Video is the fastest way to make it feel real, and most software company teams skip that step.\n\nWe turn screen recordings into motion-led product explainers with hook variants for paid and organic tests.\n\nWorth a short sample cut from your existing footage?"
    },
    email2: {
      subject: "feature clip cuts",
      body: "Hi Marcus,\n\nOne demo capture typically becomes a launch explainer plus a set of feature clips for every channel.\n\nWe deliver finished demo explainers in 3-4 days from raw Loom or screen captures, with animated UI callouts highlighting core features.\n\nOpen to one before/after example?"
    },
    email3: {
      subject: "launch video backlog",
      body: "Hi Marcus,\n\nClosing the loop here. Publishing finished video consistently is nearly always a bandwidth problem, not a content problem.\n\nIf it's backlog, we run as a quiet post-production bench on footage you supply.\n\nWorth keeping in mind for when queues spike, or is capacity completely handled?"
    }
  },
  {
    id: "medical_aesthetic_company_weak",
    segment: "medical_aesthetic",
    tier: "company",
    evidence: "weak",
    variant: "weak.o0s1a0cl1su1c210",
    email1: {
      subject: "scottsdale medical spa",
      body: "Hi,\n\nMost medical spa teams in AZ sit on usable footage already: walkthroughs, events, phone clips that never become finished video.\n\nWe take raw treatment-room phone clips and turn them into clear, compliant patient explainers delivered in 48 hours.\n\nWant a sample edit matched to your style of work?"
    },
    email2: {
      subject: "education reel pacing",
      body: "Hi,\n\nClear procedure explainers tend to convert consult inquiries better than stock photos or static galleries.\n\nWe finish provider and education footage you already capture: retention pacing, clean motion graphics, and platform-ready cuts.\n\nOpen to one before/after example?"
    },
    email3: {
      subject: "education clip backlog",
      body: "Hi,\n\nClosing the loop here. Publishing finished video consistently is nearly always a bandwidth problem, not a content problem.\n\nIf it's bandwidth, that's exactly the gap we fill: post-production only, on your media.\n\nWhen footage gets shot on your side, who finishes it, or does it wait?"
    }
  }
];

async function runEvaluation() {
  console.log("================================================================================");
  console.log("  JEV COMPREHENSIVE EVALUATION: SUBJECT LINES & 3-EMAIL SEQUENCE ARC");
  console.log("================================================================================\n");

  for (const sample of SAMPLES) {
    console.log(`--------------------------------------------------------------------------------`);
    console.log(`Evaluating Sample: ${sample.id} (${sample.segment} | ${sample.tier} | ${sample.evidence})`);
    console.log(`--------------------------------------------------------------------------------`);

    // 1. Evaluate Subject Lines
    console.log("\n>> [Part 1: Subject Line Open-Rate & Deliverability Evaluation]");
    const subjectState = `
TARGET AUDIENCE: B2B Business Owner / Agency Executive
OUTREACH CONTEXT: Cold email outreach
TOUCH 1 SUBJECT: "${sample.email1.subject}"
TOUCH 2 SUBJECT: "${sample.email2.subject}"
TOUCH 3 SUBJECT: "${sample.email3.subject}"
`;

    const subjectEval = await experimental_evaluate({
      model: 'typesafe-ai/jev',
      state: subjectState,
      questions: {
        resemblesPeerEmail: {
          type: 'score',
          instructions: 'Rate how closely these subject lines resemble a casual, 1-to-1 internal email from an industry peer rather than marketing broadcast',
          criteria: ['Obvious marketing broadcast / sales pitch', 'Standard sales outreach subject', 'Indistinguishable from casual 1-on-1 peer correspondence']
        },
        suspectedAutomated: {
          type: 'boolean',
          instructions: 'Would a busy founder or decision-maker immediately suspect these subject lines were mechanically scraped or automated?'
        },
        inboxDeliverabilityRisk: {
          type: 'score',
          instructions: 'Evaluate the likelihood that Google Workspace / Outlook spam and promotional filters let these subjects land in the Primary Inbox',
          criteria: ['High risk of Spam / Promotions tab', 'Borderline / Moderate deliverability', 'High deliverability / Primary Inbox placement']
        }
      }
    });

    const sAns = subjectEval.answers as any;
    console.log(`  - Peer Resemblance Score: ${sAns.resemblesPeerEmail?.score?.toFixed(2)} / 2.0`);
    console.log(`  - Suspected Automated/Scraped: ${sAns.suspectedAutomated?.value} (${(sAns.suspectedAutomated?.probability * 100).toFixed(1)}% prob)`);
    console.log(`  - Primary Inbox Placement Score: ${sAns.inboxDeliverabilityRisk?.score?.toFixed(2)} / 2.0`);

    // 2. Evaluate Full 3-Email Sequence Arc
    console.log("\n>> [Part 2: 3-Email Sequence Arc & Tone Progression]");
    const sequenceState = `
AUDIENCE SEGMENT: ${sample.segment}
OUTREACH TIER: ${sample.tier} (greeting rule: ${sample.tier === 'company' ? 'Strictly generic "Hi,", NO company name allowed anywhere' : 'Personal "Hi {first_name},"' })
EVIDENCE TYPE: ${sample.evidence}

=== TOUCH 1 (Day 0) ===
Subject: ${sample.email1.subject}
${sample.email1.body}

=== TOUCH 2 (Day +3) ===
Subject: ${sample.email2.subject}
${sample.email2.body}

=== TOUCH 3 (Day +7 - Breakup) ===
Subject: ${sample.email3.subject}
${sample.email3.body}
`;

    const sequenceEval = await experimental_evaluate({
      model: 'typesafe-ai/jev',
      state: sequenceState,
      questions: {
        progressionAndFreshAngle: {
          type: 'score',
          instructions: 'Does each touch in the 3-email sequence introduce a distinct perspective without repeating arguments or sounding like a copy-paste follow-up?',
          criteria: ['Repetitive / nagging sequence', 'Acceptable follow-up sequence', 'Strong progressive value across all 3 touches']
        },
        breakupToneDetached: {
          type: 'boolean',
          instructions: 'Does Email 3 (the breakup email) maintain polite professional detachment without sounding guilt-tripping, passive-aggressive, or desperate?'
        },
        objectionHandling: {
          type: 'score',
          instructions: 'How effectively does Touch 2 address the natural objection ("we already shoot video" or "we already have someone") with practical workflow clarity?',
          criteria: ['Fails to address objections', 'Moderately answers objections', 'Concisely reframes objection into an operational bandwidth/finishing benefit']
        },
        naturalnessWithoutCompanyName: {
          type: 'boolean',
          instructions: 'Does the email read smoothly and naturally without needing or missing a formal company name insertion?'
        },
        overallReplyLikelihood: {
          type: 'score',
          instructions: 'Overall assessment of cold email reply likelihood from an qualified buyer',
          criteria: ['Low likelihood / instant archive', 'Moderate likelihood of interest', 'High likelihood of earning a conversation or sample review']
        }
      }
    });

    const seqAns = sequenceEval.answers as any;
    console.log(`  - Progression & Fresh Angle: ${seqAns.progressionAndFreshAngle?.score?.toFixed(2)} / 2.0`);
    console.log(`  - Breakup Tone Polite & Detached: ${seqAns.breakupToneDetached?.value} (${(seqAns.breakupToneDetached?.probability * 100).toFixed(1)}% prob)`);
    console.log(`  - Objection Handling (Touch 2): ${seqAns.objectionHandling?.score?.toFixed(2)} / 2.0`);
    console.log(`  - Natural Voice (Without Company Name): ${seqAns.naturalnessWithoutCompanyName?.value} (${(seqAns.naturalnessWithoutCompanyName?.probability * 100).toFixed(1)}% prob)`);
    console.log(`  - Overall Reply Likelihood: ${seqAns.overallReplyLikelihood?.score?.toFixed(2)} / 2.0`);
    console.log("\n");
  }
}

runEvaluation().catch(err => {
  console.error("Evaluation failed:", err);
  process.exit(1);
});
