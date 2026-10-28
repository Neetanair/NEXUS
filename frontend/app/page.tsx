"use client";

import { useEffect, useState } from "react";

import {
  submitCheckIn,
  recordRecommendationDecision,
  getDashboard,
  completeTask,
  getLatestRecommendation,
  approveRecommendation,
  getMemories,
} from "@/lib/api";

import {
  ArrowRight,
  Check,
  Circle,
  Clock3,
  Sparkles,
  Target,
  TrendingDown,
} from "lucide-react";

export default function Home() {
  const [checkIn, setCheckIn] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [reflection, setReflection] = useState<any>(null);
  const [taskCreated, setTaskCreated] = useState(false);
  const [creatingTask, setCreatingTask] = useState(false);
  const [tasks, setTasks] = useState<any[]>([]);
  const [dashboard, setDashboard] = useState<any>(null);
  const [memories, setMemories] = useState<any[]>([]);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const data = await getDashboard();

        setDashboard(data);
        setTasks(data.tasks);
      } catch (err) {
        console.error("Failed to load dashboard:", err);
      }
    }

    async function loadLatestRecommendation() {
      try {
        const recommendation = await getLatestRecommendation();

        if (
          recommendation &&
          recommendation.status === "pending"
        ) {
          setReflection({
            id: recommendation.id,
            biggest_drift: {
              goal: recommendation.goal,
            },
            explanation: "",
            recommendation: {
              title: recommendation.title,
              description: recommendation.description,
              total_minutes: recommendation.total_minutes,
            },
          });
        } else {
          setReflection(null);
        }
      } catch (err) {
        console.error(
          "Failed to load latest recommendation:",
          err
        );
      }
    }

    async function loadMemories() {
      try {
        const data = await getMemories();
        setMemories(data);
      } catch (err) {
        console.error("Failed to load memories:", err);
      }
    }

    loadDashboard();
    loadLatestRecommendation();
    loadMemories();
  }, []);

  const handleCompleteTask = async (taskId: number) => {
    try {
      setError("");

      await completeTask(taskId);

      const updatedDashboard = await getDashboard();

      setDashboard(updatedDashboard);
      setTasks(updatedDashboard.tasks);
    } catch (err) {
      console.error("Failed to complete task:", err);
      setError("Could not complete the task.");
    }
  };

  const handleCheckIn = async () => {
    if (!checkIn.trim()) return;

    try {
      setLoading(true);
      setError("");
      setTaskCreated(false);

      const result = await submitCheckIn(checkIn);

      console.log("NEXUS CHECK-IN RESULT:", result);

      /*
       * NO DRIFT
       */
      if (!result.recommendation) {
        setReflection({
          id: 0,
          biggest_drift: null,
          explanation: result.explanation,
          recommendation: null,
        });
      } else {
        /*
         * ACTIVE DRIFT
         *
         * The check-in response already contains the
         * recommendation. We use the latest database
         * recommendation only to obtain its ID for approval.
         */
        const latestRecommendation =
          await getLatestRecommendation();

        setReflection({
          id: latestRecommendation?.id ?? 0,
          biggest_drift: result.biggest_drift,
          explanation: result.explanation,
          recommendation: result.recommendation,
        });
      }

      setCheckIn("");

      const updatedDashboard = await getDashboard();

      setDashboard(updatedDashboard);
      setTasks(updatedDashboard.tasks);
    } catch (err) {
      console.error("Check-in failed:", err);

      setError(
        "Something went wrong. Make sure FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleApproveRecommendation = async () => {
    if (!reflection?.recommendation || !reflection.id) {
      setError("No pending recommendation found.");
      return;
    }

    try {
      setCreatingTask(true);
      setError("");

      await approveRecommendation(reflection.id);

      setTaskCreated(true);

      const updatedDashboard = await getDashboard();

      setDashboard(updatedDashboard);
      setTasks(updatedDashboard.tasks);
    } catch (err) {
      console.error(
        "Failed to approve recommendation:",
        err
      );

      setError(
        "Could not add the recommendation to your tasks."
      );
    } finally {
      setCreatingTask(false);
    }
  };

  const handleDismissRecommendation = async () => {
    if (
      !reflection?.recommendation ||
      !reflection?.biggest_drift
    ) {
      return;
    }

    try {
      setError("");

      await recordRecommendationDecision({
        goal: reflection.biggest_drift.goal,
        recommendation_title:
          reflection.recommendation.title,
        decision: "dismissed",
      });

      setReflection(null);
      setTaskCreated(false);
    } catch (err) {
      console.error("Failed to save decision:", err);
      setError("Could not save your decision.");
    }
  };

  return (
    <main className="min-h-screen bg-[#08090d] text-white">
      <div className="mx-auto max-w-6xl px-6 py-8">

        {/* Header */}
        <header className="mb-10 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-cyan-400" />

              <h1 className="text-xl font-semibold tracking-tight">
                NEXUS
              </h1>
            </div>

            <p className="mt-1 text-sm text-zinc-500">
              Intent-aware personal AI
            </p>
          </div>

          <div className="text-right">
            <p className="text-sm text-zinc-400">
              Good evening
            </p>

            <p className="text-xs text-zinc-600">
              Your day, intentionally
            </p>
          </div>
        </header>

        {/* Main grid */}
        <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">

          {/* Focus */}
          <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-7">
            <div className="mb-7 flex items-center justify-between">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-zinc-500">
                  Your focus
                </p>

                {!dashboard ? (
                  <h2 className="mt-2 text-2xl font-semibold">
                    Loading focus...
                  </h2>
                ) : dashboard.biggest_drift ? (
                  <h2 className="mt-2 text-2xl font-semibold">
                    {dashboard.biggest_drift.goal}
                  </h2>
                ) : (
                  <h2 className="mt-2 text-2xl font-semibold">
                    All goals on track
                  </h2>
                )}
              </div>

              {dashboard?.biggest_drift && (
                <span className="rounded-full border border-red-400/20 bg-red-400/10 px-3 py-1 text-xs font-medium text-red-300">
                  {dashboard.biggest_drift.priority} priority
                </span>
              )}
            </div>

            {!dashboard ? (
              <p className="text-sm text-zinc-500">
                Loading your current focus...
              </p>
            ) : dashboard.biggest_drift ? (
              <>
                <div className="mb-3 flex items-end justify-between">
                  <div>
                    <span className="text-3xl font-semibold">
                      {dashboard.biggest_drift.completed_hours.toFixed(
                        1
                      )}
                    </span>

                    <span className="ml-1 text-sm text-zinc-500">
                      /{" "}
                      {dashboard.biggest_drift.target_hours.toFixed(
                        1
                      )}{" "}
                      hrs
                    </span>
                  </div>

                  <Target className="h-5 w-5 text-zinc-600" />
                </div>

                {/* Progress */}
                <div className="h-2 overflow-hidden rounded-full bg-white/10">
                  <div
                    className="h-full rounded-full bg-cyan-400 transition-all duration-500"
                    style={{
                      width: `${Math.min(
                        (dashboard.biggest_drift.completed_hours /
                          dashboard.biggest_drift.target_hours) *
                          100,
                        100
                      )}%`,
                    }}
                  />
                </div>

                {/* Drift */}
                <div className="mt-8 rounded-2xl border border-amber-400/10 bg-amber-400/[0.04] p-5">
                  <div className="flex gap-3">
                    <TrendingDown className="mt-0.5 h-5 w-5 shrink-0 text-amber-400" />

                    <div>
                      <p className="text-sm font-medium text-amber-300">
                        Biggest drift
                      </p>

                      <p className="mt-2 text-sm leading-6 text-zinc-400">
                        {dashboard.biggest_drift.goal} currently has
                        the largest gap between planned and completed
                        progress.
                      </p>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="rounded-2xl border border-emerald-400/10 bg-emerald-400/[0.04] p-5">
                <div className="flex gap-3">
                  <Check className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400" />

                  <div>
                    <p className="text-sm font-medium text-emerald-300">
                      You're on track
                    </p>

                    <p className="mt-2 text-sm leading-6 text-zinc-400">
                      All of your active goals are currently on
                      track. No intervention is needed right now.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* Recommendation */}
          <section className="rounded-3xl border border-cyan-400/10 bg-cyan-400/[0.03] p-7">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-cyan-400" />

              <p className="text-xs font-medium uppercase tracking-[0.2em] text-cyan-400">
                Nexus recommends
              </p>
            </div>

            {/* Active recommendation */}
            {reflection?.recommendation ? (
              <>
                <h2 className="mt-5 text-xl font-semibold">
                  {reflection.recommendation.title}
                </h2>

                
                <div className="mt-3 text-sm leading-6 text-zinc-400">
                  <p>{reflection.explanation}</p>

                  {reflection.personalized && reflection.memory_used && (
                    <div className="mt-4 rounded-2xl border border-cyan-400/10 bg-cyan-400/5 p-4">
                      <p className="text-xs font-medium uppercase tracking-[0.15em] text-cyan-400">
                        🧠 Personalized from memory
                      </p>

                      <p className="mt-2 text-sm leading-6 text-zinc-400">
                        NEXUS used this memory when choosing your recommendation:
                      </p>

                      <p className="mt-2 text-sm leading-6 text-zinc-300">
                        "{reflection.memory_used}"
                      </p>
                    </div>
                  )}
                </div>

                <p className="mt-3 text-sm leading-6 text-zinc-500">
                  {reflection.recommendation.description}
                </p>

                <div className="mt-6 flex items-center gap-2 text-sm text-zinc-500">
                  <Clock3 className="h-4 w-4" />

                  {reflection.recommendation.total_minutes} minutes
                </div>

                <button
                  disabled={creatingTask || taskCreated}
                  onClick={handleApproveRecommendation}
                  className="mt-7 flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-black transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {taskCreated ? (
                    <>
                      <Check className="h-4 w-4" />
                      Added to tasks
                    </>
                  ) : creatingTask ? (
                    "Adding..."
                  ) : (
                    <>
                      Do this
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                      </button>
                  {taskCreated && (
                    <div className="mt-4 rounded-2xl border border-emerald-400/10 bg-emerald-400/5 p-4">
                      <p className="text-xs font-medium uppercase tracking-[0.15em] text-emerald-400">
                        ✓ Action created
                      </p>

                      <p className="mt-2 text-sm leading-6 text-zinc-400">
                        NEXUS turned this recommendation into a task. Complete it to
                        update your goal progress.
                      </p>
                    </div>
                  )}
            

                <button
                  disabled={creatingTask || taskCreated}
                  onClick={handleDismissRecommendation}
                  className="mt-3 w-full rounded-xl border border-white/10 px-4 py-3 text-sm text-zinc-400 transition hover:bg-white/5 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Not now
                </button>
              </>
            ) : reflection ? (
              /* No drift after check-in */
              <>
                <h2 className="mt-5 text-xl font-semibold">
                  You're on track
                </h2>

                <p className="mt-3 text-sm leading-6 text-zinc-400">
                  {reflection.explanation}
                </p>

                <div className="mt-6 flex items-center gap-2 text-sm text-emerald-400">
                  <Check className="h-4 w-4" />
                  No intervention needed
                </div>
              </>
            ) : (
              /* Before check-in */
              <>
                <h2 className="mt-5 text-xl font-semibold">
                  Your next step
                </h2>

                <p className="mt-3 text-sm leading-6 text-zinc-400">
                  Check in with NEXUS to receive a personalized
                  recommendation based on how your day actually went.
                </p>

                <div className="mt-6 flex items-center gap-2 text-sm text-zinc-500">
                  <Clock3 className="h-4 w-4" />
                  Waiting for your check-in
                </div>
              </>
            )}
          </section>
        </div>

        {/* Check in */}
        <section className="mt-6 rounded-3xl border border-white/10 bg-white/[0.03] p-7">
          <div className="mb-5">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-zinc-500">
              Check in
            </p>

            <h2 className="mt-2 text-xl font-semibold">
              What did you do today?
            </h2>
          </div>

          <textarea
            value={checkIn}
            onChange={(e) => setCheckIn(e.target.value)}
            placeholder="Tell NEXUS what happened today..."
            className="min-h-32 w-full resize-none rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-white outline-none placeholder:text-zinc-600 focus:border-cyan-400/40"
          />

          <div className="mt-4 flex items-center justify-end gap-4">
            <button
              disabled={!checkIn.trim() || loading}
              onClick={handleCheckIn}
              className="rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading
                ? "NEXUS is thinking..."
                : "Check in"}
            </button>
          </div>

          {error && (
            <p className="mt-3 text-right text-sm text-red-400">
              {error}
            </p>
          )}
        </section>

        {/* Bottom grid */}
        <div className="mt-6 grid gap-6 md:grid-cols-3">

          {/* Activity */}
          <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-7">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-zinc-500">
              Today
            </p>

            <div className="mt-5 space-y-4">
              {!dashboard ? (
                <p className="text-sm text-zinc-600">
                  Loading today's activity...
                </p>
              ) : dashboard.activities.length === 0 ? (
                <p className="text-sm text-zinc-600">
                  No activities logged today.
                </p>
              ) : (
                dashboard.activities.map((activity: any) => (
                  <Activity
                    key={activity.id}
                    title={activity.title}
                    duration={`${activity.hours}h`}
                  />
                ))
              )}
            </div>
          </section>

          {/* Tasks */}
          <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-7">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-zinc-500">
              Tasks
            </p>

            <div className="mt-5">
              {tasks.length === 0 ? (
                <p className="text-sm text-zinc-600">
                  No tasks yet.
                </p>
              ) : (
                <div className="space-y-4">
                  {tasks.map((task) => (
                    <Task
                      key={task.id}
                      id={task.id}
                      title={task.title}
                      duration={`${task.duration_minutes} min`}
                      status={task.status}
                      onComplete={handleCompleteTask}
                    />
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Memory */}
          <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-7">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-cyan-400" />

              <p className="text-xs font-medium uppercase tracking-[0.2em] text-zinc-500">
                NEXUS remembers
              </p>
            </div>

            <div className="mt-5 space-y-4">
              {memories.length === 0 ? (
                <p className="text-sm text-zinc-600">
                  NEXUS hasn't learned anything about you yet.
                </p>
              ) : (
                memories.slice(0, 4).map((memory) => (
                  <div
                    key={memory.id}
                    className="rounded-2xl border border-white/5 bg-black/20 p-4"
                  >
                    <p className="text-xs font-medium uppercase tracking-wide text-cyan-400">
                      {memory.type === "preference" && "🧠 Preference"}
                      {memory.type === "goal" && "🎯 Goal"}
                      {memory.type === "commitment" && "🤝 Commitment"}
                      {memory.type === "context" && "📌 Context"}
                    </p>

                    <p className="mt-2 text-sm leading-6 text-zinc-300">
                      {memory.content}
                    </p>
                  </div>
                ))
              )}
            </div>

            {memories.length > 4 && (
              <p className="mt-4 text-xs text-zinc-600">
                Showing your most relevant memories.
              </p>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}

function Activity({
  title,
  duration,
}: {
  title: string;
  duration: string;
}) {
  return (
    <div className="flex items-center justify-between border-b border-white/5 pb-4 last:border-0 last:pb-0">
      <div className="flex items-center gap-3">
        <Check className="h-4 w-4 text-emerald-400" />

        <span className="text-sm text-zinc-300">
          {title}
        </span>
      </div>

      <span className="text-sm text-zinc-600">
        {duration}
      </span>
    </div>
  );
}

function Task({
  id,
  title,
  duration,
  status,
  onComplete,
}: {
  id: number;
  title: string;
  duration: string;
  status: string;
  onComplete: (id: number) => void;
}) {
  const completed = status === "completed";

  return (
    <button
      type="button"
      onClick={() => {
        if (!completed) {
          onComplete(id);
        }
      }}
      className="flex w-full items-start gap-3 text-left"
    >
      {completed ? (
        <Check className="mt-0.5 h-4 w-4 text-emerald-400" />
      ) : (
        <Circle className="mt-0.5 h-4 w-4 text-zinc-600" />
      )}

      <div className="flex-1">
        <p
          className={`text-sm ${
            completed
              ? "text-zinc-600 line-through"
              : "text-zinc-300"
          }`}
        >
          {title}
        </p>

        <div className="mt-1 flex items-center gap-1 text-xs text-zinc-600">
          <Clock3 className="h-3 w-3" />
          {duration}
        </div>
      </div>
    </button>
  );
}