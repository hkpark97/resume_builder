const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export function getToken() {
  return localStorage.getItem("resumagic_token");
}

export function setToken(token) {
  localStorage.setItem("resumagic_token", token);
}

export function clearToken() {
  localStorage.removeItem("resumagic_token");
}

async function request(path, options = {}) {
  const token = getToken();

  const headers = {
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const text = await response.text();

  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!response.ok) {
    const detail = data?.detail || data?.message || data || "Request failed";
    throw new Error(
      typeof detail === "string" ? detail : JSON.stringify(detail),
    );
  }

  return data;
}

export const api = {
  health: () => request("/health"),

  publicAnalyze: ({
    resumeFile,
    jobFile,
    jobTitle,
    company,
    jobDescription,
  }) => {
    const form = new FormData();

    form.append("resume_file", resumeFile);

    if (jobFile) {
      form.append("job_file", jobFile);
    }

    form.append("job_title", jobTitle || "");
    form.append("company", company || "");
    form.append("job_description", jobDescription || "");

    return request("/public/analyze", {
      method: "POST",
      body: form,
    });
  },

  signup: (payload) =>
    request("/auth/signup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }),

  login: (payload) =>
    request("/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }),

  me: () => request("/auth/me"),

  saveAnalysis: (payload) =>
    request("/saved/analysis", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }),

  listSavedAnalysis: () => request("/saved/analysis"),

  saveFeedback: (payload) =>
    request("/saved/feedback", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }),

  updateAnalysis: (analysisId, payload) =>
    request(`/saved/analysis/${analysisId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }),

  deleteAnalysis: (analysisId) =>
    request(`/saved/analysis/${analysisId}`, {
      method: "DELETE",
    }),

  reorderAnalysis: (orderedIds) =>
    request("/saved/analysis/reorder", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ordered_ids: orderedIds }),
    }),
};
