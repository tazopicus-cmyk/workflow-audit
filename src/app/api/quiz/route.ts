import { NextRequest, NextResponse } from "next/server";
import { scoringEngine } from "@/lib/scoring";

export async function POST(request: NextRequest) {
  try {
    const { email, businessName, answers } = await request.json();

    if (!email || !answers) {
      return NextResponse.json(
        { error: "Email and answers are required" },
        { status: 400 }
      );
    }

    // Score the quiz
    const results = scoringEngine(answers);

    // Build the email content
    const emailContent = buildRoadmapEmail(businessName, results);

    // Send the email
    await sendEmail(email, businessName || "Your Business", emailContent);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Quiz submission error:", error);
    return NextResponse.json(
      { error: "Failed to process quiz" },
      { status: 500 }
    );
  }
}

interface ScoreResult {
  id: string;
  category: string;
  question: string;
  frequency: number;
  time: number;
  frustration: number;
  score: number;
  tier: "HIGH" | "MEDIUM" | "LOW" | "SKIP";
}

function scoringEngine(answers: Record<string, number>): ScoreResult[] {
  // Questions with their weights: [frequency_weight, time_weight, frustration_weight]
  // We map each answer to a (frequency, time, frustration) tuple
  const questionMetrics: Record<string, [number, number, number]> = {
    q1: [answers.q1, 0, 0], // frequency only
    q2: [0, answers.q2, 0], // time to respond
    q3: [0, answers.q3, answers.q3], // time + frustration (dreaded task)
    q4: [answers.q4, 0, 0], // frequency only
    q5: [0, answers.q5, answers.q5], // creation time + frustration
    q6: [answers.q6, 0, 0], // frequency
    q7: [0, answers.q7, answers.q7], // planning time + frustration
    q8: [answers.q8, 0, 0], // frequency
    q9: [0, answers.q9, answers.q9], // time + frustration
    q10: [answers.q10, 0, 0], // frequency
    q11: [0, answers.q11, answers.q11], // time + frustration
    q12: [answers.q12, 0, 0], // frequency
    q13: [answers.q13, 0, Math.max(answers.q13, 3)], // frequency + high frustration if rarely
    q14: [0, answers.q14, Math.max(answers.q14, 3)], // time + frustration
    q15: [answers.q15, 0, 0], // frequency
  };

  const questions = [
    { id: "q1", category: "Client Communication", question: "Emailing clients" },
    { id: "q2", category: "Client Communication", question: "Responding to client messages" },
    { id: "q3", category: "Client Communication", question: "Client invoicing & payment follow-ups" },
    { id: "q4", category: "Content & Marketing", question: "Social media posting" },
    { id: "q5", category: "Content & Marketing", question: "Creating social media content" },
    { id: "q6", category: "Content & Marketing", question: "Newsletter & email updates" },
    { id: "q7", category: "Content & Marketing", question: "Content planning & ideation" },
    { id: "q8", category: "Operations & Logistics", question: "Scheduling & appointments" },
    { id: "q9", category: "Operations & Logistics", question: "Inventory & supply management" },
    { id: "q10", category: "Operations & Logistics", question: "Administrative tasks & data entry" },
    { id: "q11", category: "Finance & Admin", question: "Invoice creation & payment tracking" },
    { id: "q12", category: "Finance & Admin", question: "Checking finances & cash flow" },
    { id: "q13", category: "Lead & Customer Follow-up", question: "Following up with new leads" },
    { id: "q14", category: "Lead & Customer Follow-up", question: "Review requests & testimonials" },
    { id: "q15", category: "Lead & Customer Follow-up", question: "Re-engaging past customers" },
  ];

  const results: ScoreResult[] = questions.map((q) => {
    const [freq, time, frust] = questionMetrics[q.id];
    const score = freq * time * (frust || 1);
    let tier: ScoreResult["tier"] = "SKIP";
    if (score >= 80) tier = "HIGH";
    else if (score >= 50) tier = "MEDIUM";
    else if (score >= 25) tier = "LOW";

    return {
      id: q.id,
      category: q.category,
      question: q.question,
      frequency: freq,
      time: time,
      frustration: frust || 1,
      score,
      tier,
    };
  });

  return results.sort((a, b) => b.score - a.score);
}

function getTierEmoji(tier: ScoreResult["tier"]): string {
  switch (tier) {
    case "HIGH":
      return "🔴";
    case "MEDIUM":
      return "🟡";
    case "LOW":
      return "🟢";
    default:
      return "⚪";
  }
}

function buildRoadmapEmail(
  businessName: string,
  results: ScoreResult[]
): string {
  const top3 = results.filter((r) => r.tier !== "SKIP").slice(0, 3);
  const quickWin = results[0];

  const targetsList = top3
    .map(
      (t, i) => `
${i + 1}. ${getTierEmoji(t.tier)} ${t.question}
   Score: ${t.score}/125 | ${t.category}
   `
    )
    .join("\n");

  const recommendations = top3.map((t) => {
    let rec = "";
    if (t.category === "Client Communication") {
      rec = "→ Set up templated responses + email scheduling";
    } else if (t.category === "Content & Marketing") {
      rec = "→ Batch content creation with AI assistance";
    } else if (t.category === "Operations & Logistics") {
      rec = "→ Automate with scheduling tools or virtual assistants";
    } else if (t.category === "Finance & Admin") {
      rec = "→ Use invoicing software with automatic reminders";
    } else if (t.category === "Lead & Customer Follow-up") {
      rec = "→ Set up automated follow-up sequences";
    }
    return `${t.question}: ${rec}`;
  });

  return `
Your 5-Minute Business Auto-Audit Results
${businessName ? `for ${businessName}` : ""}

========================================

🔴 YOUR TOP 3 AUTOMATION TARGETS

${targetsList}

========================================

YOUR QUICK WIN (do this today):
${quickWin.question}
Score: ${quickWin.score}/125

========================================

AUTOMATION RECOMMENDATIONS:

${recommendations.map((r, i) => `${i + 1}. ${r}`).join("\n\n")}

========================================

Need help automating these? Reply to this email or visit tindogdigital.tech

—
Built by Tin Dog Digital
  `.trim();
}

async function sendEmail(
  to: string,
  businessName: string,
  content: string
): Promise<void> {
  // TODO: Implement email sending
  // Options:
  // 1. Resend (resend.com) - recommended for Next.js
  // 2. SendGrid
  // 3. AWS SES
  // 4. Nodemailer with SMTP

  console.log("EMAIL WOULD BE SENT TO:", to);
  console.log("SUBJECT: Your Automation Roadmap");
  console.log("CONTENT:", content);

  // For now, just log it. Implementation depends on email provider setup.
  // The actual email sending will be implemented once we know which provider.
}