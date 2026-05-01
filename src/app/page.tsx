"use client";

import { useState } from "react";

const questions = [
  // Category 1: Client Communication
  {
    id: "q1",
    category: "Client Communication",
    question: "How often do you send emails to clients or customers?",
    options: [
      { value: 5, label: "Multiple times a day" },
      { value: 4, label: "Once a day" },
      { value: 3, label: "A few times a week" },
      { value: 2, label: "Once a week" },
      { value: 1, label: "Rarely / never" },
    ],
  },
  {
    id: "q2",
    category: "Client Communication",
    question: "How long does it typically take to respond to a client email or text?",
    options: [
      { value: 5, label: "30+ minutes" },
      { value: 4, label: "15-30 minutes" },
      { value: 3, label: "5-15 minutes" },
      { value: 2, label: "1-5 minutes" },
      { value: 1, label: "I respond immediately" },
    ],
  },
  {
    id: "q3",
    category: "Client Communication",
    question: "How much time per week do you spend on client invoicing or payment follow-ups?",
    options: [
      { value: 5, label: "5+ hours" },
      { value: 4, label: "3-5 hours" },
      { value: 3, label: "1-3 hours" },
      { value: 2, label: "30 min - 1 hour" },
      { value: 1, label: "Less than 30 min" },
    ],
  },
  // Category 2: Content & Marketing
  {
    id: "q4",
    category: "Content & Marketing",
    question: "How often do you post on social media for your business?",
    options: [
      { value: 5, label: "Daily" },
      { value: 4, label: "3-4x per week" },
      { value: 3, label: "1-2x per week" },
      { value: 2, label: "A few times a month" },
      { value: 1, label: "Rarely / never" },
    ],
  },
  {
    id: "q5",
    category: "Content & Marketing",
    question: "When you create a social post, how long does it take from idea to published?",
    options: [
      { value: 5, label: "30+ minutes per post" },
      { value: 4, label: "15-30 minutes per post" },
      { value: 3, label: "5-15 minutes per post" },
      { value: 2, label: "1-5 minutes per post" },
      { value: 1, label: "I batch-create a week's posts in under an hour" },
    ],
  },
  {
    id: "q6",
    category: "Content & Marketing",
    question: "How often do you send a newsletter or email update to your audience?",
    options: [
      { value: 5, label: "Weekly or more" },
      { value: 4, label: "Every 2-3 weeks" },
      { value: 3, label: "Monthly" },
      { value: 2, label: "A few times a year" },
      { value: 1, label: "Never" },
    ],
  },
  {
    id: "q7",
    category: "Content & Marketing",
    question: "How much time per week do you spend thinking about or planning what content to post?",
    options: [
      { value: 5, label: "2+ hours" },
      { value: 4, label: "1-2 hours" },
      { value: 3, label: "30 min - 1 hour" },
      { value: 2, label: "10-30 minutes" },
      { value: 1, label: "I don't plan, I just post" },
    ],
  },
  // Category 3: Operations & Logistics
  {
    id: "q8",
    category: "Operations & Logistics",
    question: "How often do you handle scheduling or appointment-related tasks?",
    options: [
      { value: 5, label: "Daily" },
      { value: 4, label: "A few times a week" },
      { value: 3, label: "Weekly" },
      { value: 2, label: "A few times a month" },
      { value: 1, label: "Rarely / never" },
    ],
  },
  {
    id: "q9",
    category: "Operations & Logistics",
    question: "How much time per week do you spend on inventory, supplies, or orders?",
    options: [
      { value: 5, label: "5+ hours" },
      { value: 4, label: "3-5 hours" },
      { value: 3, label: "1-3 hours" },
      { value: 2, label: "30 min - 1 hour" },
      { value: 1, label: "Less than 30 min" },
    ],
  },
  {
    id: "q10",
    category: "Operations & Logistics",
    question: "How often do you do administrative tasks like filing, data entry, or spreadsheets?",
    options: [
      { value: 5, label: "Daily" },
      { value: 4, label: "A few times a week" },
      { value: 3, label: "Weekly" },
      { value: 2, label: "A few times a month" },
      { value: 1, label: "Rarely" },
    ],
  },
  // Category 4: Finance & Admin
  {
    id: "q11",
    category: "Finance & Admin",
    question: "How much time per week do you spend creating invoices or tracking payments?",
    options: [
      { value: 5, label: "3+ hours" },
      { value: 4, label: "1-3 hours" },
      { value: 3, label: "30 min - 1 hour" },
      { value: 2, label: "10-30 minutes" },
      { value: 1, label: "I have a system that handles most of it" },
    ],
  },
  {
    id: "q12",
    category: "Finance & Admin",
    question: "How often do you check your business finances or review cash flow?",
    options: [
      { value: 5, label: "Daily" },
      { value: 4, label: "A few times a week" },
      { value: 3, label: "Weekly" },
      { value: 2, label: "Monthly" },
      { value: 1, label: "Rarely / never" },
    ],
  },
  // Category 5: Lead & Customer Follow-up
  {
    id: "q13",
    category: "Lead & Customer Follow-up",
    question: "How often do you follow up with new leads who haven't booked yet?",
    options: [
      { value: 5, label: "Every day" },
      { value: 4, label: "A few times a week" },
      { value: 3, label: "When I remember" },
      { value: 2, label: "Rarely" },
      { value: 1, label: "I don't have a system for this" },
    ],
  },
  {
    id: "q14",
    category: "Lead & Customer Follow-up",
    question: "How much time per week do you spend on review requests or getting testimonials?",
    options: [
      { value: 5, label: "2+ hours" },
      { value: 4, label: "1-2 hours" },
      { value: 3, label: "30 min - 1 hour" },
      { value: 2, label: "10-30 minutes" },
      { value: 1, label: "I don't do this consistently" },
    ],
  },
  {
    id: "q15",
    category: "Lead & Customer Follow-up",
    question: "How often do you re-engage past customers for repeat business or referrals?",
    options: [
      { value: 5, label: "Monthly or more" },
      { value: 4, label: "Quarterly" },
      { value: 3, label: "A few times a year" },
      { value: 2, label: "Once a year or less" },
      { value: 1, label: "Never" },
    ],
  },
];

type Answers = Record<string, number>;

export default function QuizPage() {
  const [step, setStep] = useState<"email" | "quiz" | "submitting" | "done">("email");
  const [email, setEmail] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [answers, setAnswers] = useState<Answers>({});
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [error, setError] = useState("");

  const handleAnswer = (questionId: string, value: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      setStep("submitting");
      submitQuiz();
    }
  };

  const handleBack = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const submitQuiz = async () => {
    try {
      const response = await fetch("/api/quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, businessName, answers }),
      });

      if (response.ok) {
        setStep("done");
      } else {
        setError("Something went wrong. Please try again.");
        setStep("quiz");
      }
    } catch {
      setError("Failed to submit. Please try again.");
      setStep("quiz");
    }
  };

  const q = questions[currentQuestion];
  const progress = ((currentQuestion + 1) / questions.length) * 100;
  const currentAnswer = answers[q.id];

  return (
    <div className="min-h-screen bg-zinc-50 py-12 px-4">
      <div className="mx-auto max-w-2xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="mb-2 text-3xl font-bold text-zinc-900">
            The 5-Minute Business Auto-Audit
          </h1>
          <p className="text-zinc-600">
            Answer 15 questions about your daily tasks. Get a ranked list of what to automate first.
          </p>
        </div>

        {/* Progress bar */}
        {step === "quiz" && (
          <div className="mb-8">
            <div className="flex justify-between text-sm text-zinc-500 mb-2">
              <span>Question {currentQuestion + 1} of {questions.length}</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-zinc-200">
              <div
                className="h-2 rounded-full bg-indigo-600 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Email capture */}
        {step === "email" && (
          <div className="rounded-2xl bg-white p-8 shadow-lg">
            <h2 className="mb-4 text-xl font-semibold text-zinc-900">
              Where should we send your Automation Roadmap?
            </h2>
            <p className="mb-6 text-zinc-600">
              After you complete the quiz, we&apos;ll email you a personalized report with your top automation targets.
            </p>
            <div className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-zinc-700">
                  Your Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@yourbusiness.com"
                  className="w-full rounded-lg border border-zinc-300 px-4 py-3 text-zinc-900 placeholder-zinc-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-zinc-700">
                  Business Name (optional)
                </label>
                <input
                  type="text"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  placeholder="Your Business LLC"
                  className="w-full rounded-lg border border-zinc-300 px-4 py-3 text-zinc-900 placeholder-zinc-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
              <button
                onClick={() => email && setStep("quiz")}
                disabled={!email}
                className="w-full rounded-lg bg-indigo-600 px-6 py-3 font-semibold text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-zinc-300"
              >
                Start the Quiz →
              </button>
            </div>
          </div>
        )}

        {/* Quiz question */}
        {step === "quiz" && (
          <div className="rounded-2xl bg-white p-8 shadow-lg">
            <p className="mb-2 text-sm font-medium text-indigo-600">
              {q.category}
            </p>
            <h2 className="mb-6 text-xl font-semibold text-zinc-900">
              {q.question}
            </h2>
            <div className="space-y-3">
              {q.options.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleAnswer(q.id, option.value)}
                  className={`w-full rounded-lg border-2 px-4 py-3 text-left transition-all ${
                    currentAnswer === option.value
                      ? "border-indigo-600 bg-indigo-50 text-indigo-900"
                      : "border-zinc-200 text-zinc-700 hover:border-zinc-300 hover:bg-zinc-50"
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <div className="mt-6 flex gap-3">
              {currentQuestion > 0 && (
                <button
                  onClick={handleBack}
                  className="rounded-lg border border-zinc-300 px-4 py-2 text-zinc-700 transition-colors hover:bg-zinc-100"
                >
                  ← Back
                </button>
              )}
              <button
                onClick={handleNext}
                disabled={!currentAnswer}
                className="flex-1 rounded-lg bg-indigo-600 px-4 py-2 font-semibold text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-zinc-300"
              >
                {currentQuestion === questions.length - 1 ? "Get My Results" : "Next →"}
              </button>
            </div>
          </div>
        )}

        {/* Submitting */}
        {step === "submitting" && (
          <div className="rounded-2xl bg-white p-12 text-center shadow-lg">
            <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-zinc-200 border-t-indigo-600" />
            <h2 className="mb-2 text-xl font-semibold text-zinc-900">
              Analyzing your workflow...
            </h2>
            <p className="text-zinc-600">
              We&apos;re scoring your answers and building your automation roadmap.
            </p>
          </div>
        )}

        {/* Done */}
        {step === "done" && (
          <div className="rounded-2xl bg-white p-8 text-center shadow-lg">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
              <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="mb-2 text-xl font-semibold text-zinc-900">
              Your Automation Roadmap is on its way!
            </h2>
            <p className="text-zinc-600">
              Check <span className="font-medium text-zinc-900">{email}</span> for your personalized automation roadmap. It usually arrives within 2 minutes.
            </p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-4 rounded-lg bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {/* Footer */}
        <p className="mt-8 text-center text-sm text-zinc-500">
          Built by{" "}
          <a href="https://tindogdigital.tech" className="text-indigo-600 hover:underline">
            Tin Dog Digital
          </a>
        </p>
      </div>
    </div>
  );
}