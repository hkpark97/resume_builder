const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
export function getToken() {
  return localStorage.getItem("resumagic_token");
}
export function setToken(t) {
  localStorage.setItem("resumagic_token", t);
}
export function clearToken() {
  localStorage.removeItem("resumagic_token");
}
async function request(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const detail = data?.detail || data?.message || data || "Request failed";
    throw new Error(
      typeof detail === "string" ? detail : JSON.stringify(detail),
    );
  }
  return data;
}
export const api = {
  health: () => request("/health"),
  publicAnalyze: ({ resumeFile, jobFile, jobTitle, company, jobDescription }) => {
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
};
