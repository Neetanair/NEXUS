const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function submitCheckIn(text: string) {
  const response = await fetch(`${API_URL}/check-in`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error("Failed to submit check-in");
  }

  return response.json();
}


export async function getTasks() {
  const response = await fetch(`${API_URL}/tasks`);

  if (!response.ok) {
    throw new Error("Failed to load tasks");
  }

  return response.json();
}


export async function createTask(task: {
  title: string;
  description: string;
  duration_minutes: number;
}) {
  const response = await fetch(`${API_URL}/tasks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(task),
  });

  if (!response.ok) {
    throw new Error("Failed to create task");
  }

  return response.json();
}

export async function recordRecommendationDecision(decision: {
  goal: string;
  recommendation_title: string;
  decision: "approved" | "dismissed";
}) {
  const response = await fetch(
    `${API_URL}/recommendations/decision`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(decision),
    }
  );

  if (!response.ok) {
    throw new Error("Failed to record recommendation decision");
  }

  return response.json();
}

export async function getDashboard() {
  const response = await fetch(`${API_URL}/dashboard`);

  if (!response.ok) {
    throw new Error("Failed to load dashboard");
  }

  return response.json();
}

export async function completeTask(taskId: number) {
  const response = await fetch(
    `${API_URL}/tasks/${taskId}/complete`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to complete task");
  }

  return response.json();
}

export async function getLatestRecommendation() {
  const response = await fetch(
    `${API_URL}/recommendations/latest`
  );

  if (!response.ok) {
    throw new Error("Failed to load latest recommendation");
  }

  return response.json();
}


export async function approveRecommendation(
  recommendationId: number
) {
  const response = await fetch(
    `${API_URL}/recommendations/${recommendationId}/approve`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to approve recommendation");
  }

  return response.json();
}


export async function getMemories() {
  const response = await fetch(
    `${API_URL}/memories`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch memories");
  }

  return response.json();
}