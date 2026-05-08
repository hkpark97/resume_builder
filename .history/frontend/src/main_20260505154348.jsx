import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { api, getToken, setToken, clearToken } from "./api";
import "./styles.css";

function App() {
  const params = new URLSearchParams(window.location.search);
  const resetTokenFromUrl = params.get("token");
  const resetEmailFromUrl = params.get("email");

  const [page, setPage] = useState(
    resetTokenFromUrl && resetEmailFromUrl ? "reset-password" : "home",
  );

  const [token, setTokenState] = useState(getToken());
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState("checking");

  const [resumeFile, setResumeFile] = useState(null);
  const [jobFile, setJobFile] = useState(null);
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [saved, setSaved] = useState([]);

  const [authMode, setAuthMode] = useState("login");
  const [auth, setAuth] = useState({
    email: "",
    password: "",
    full_name: "",
  });

  const [resetEmail, setResetEmail] = useState(resetEmailFromUrl || "");
  const [resetToken, setResetToken] = useState(resetTokenFromUrl || "");
  const [newPassword, setNewPassword] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [changeNewPassword, setChangeNewPassword] = useState("");

  const [feedback, setFeedback] = useState({
    rating: 5,
    applied: false,
    interview_received: false,
    user_notes: "",
  });

  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loggedIn = Boolean(token);

  useEffect(() => {
    api
      .health()
      .then(() => setStatus("online"))
      .catch(() => setStatus("offline"));
  }, []);

  useEffect(() => {
    if (token) {
      api
        .me()
        .then(setUser)
        .catch(() => {
          clearToken();
          setTokenState(null);
        });

      loadSaved();
    }
  }, [token]);

  async function loadSaved() {
    try {
      setSaved(await api.listSavedAnalysis());
    } catch {
      setSaved([]);
    }
  }

  async function analyze(e) {
    e.preventDefault();
    setError("");
    setNotice("");

    if (!resumeFile) {
      setError("Please upload your resume.");
      return;
    }

    if (!jobFile && !jobDescription.trim()) {
      setError("Please paste a job description or upload a job posting file.");
      return;
    }

    try {
      setLoading("Analyzing resume...");

      const result = await api.publicAnalyze({
        resumeFile,
        jobFile,
        jobTitle,
        company,
        jobDescription,
      });

      setAnalysis(result);
      setNotice("Analysis complete.");

      setTimeout(() => {
        document
          .getElementById("result")
          ?.scrollIntoView({ behavior: "smooth" });
      }, 50);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function handleAuth(e) {
    e.preventDefault();
    setError("");
    setNotice("");

    try {
      setLoading(
        authMode === "signup" ? "Creating account..." : "Logging in...",
      );

      const payload =
        authMode === "signup"
          ? auth
          : {
              email: auth.email,
              password: auth.password,
            };

      const result =
        authMode === "signup"
          ? await api.signup(payload)
          : await api.login(payload);

      setToken(result.access_token);
      setTokenState(result.access_token);
      setNotice(authMode === "signup" ? "Account created." : "Logged in.");
      setPage("dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function requestPasswordReset(e) {
    e.preventDefault();
    setError("");
    setNotice("");

    try {
      setLoading("Requesting password reset...");

      const result = await api.requestPasswordReset({
        email: resetEmail,
      });

      setNotice(
        result.message ||
          "If this email exists, password reset instructions will be sent.",
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function resetPassword(e) {
    e.preventDefault();
    setError("");
    setNotice("");

    try {
      setLoading("Resetting password...");

      await api.resetPassword({
        email: resetEmail,
        reset_token: resetToken,
        new_password: newPassword,
      });

      setNotice("Password reset complete. You can now login.");
      setPage("account");
      setAuthMode("login");

      window.history.replaceState({}, document.title, "/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function changePassword(e) {
    e.preventDefault();
    setError("");
    setNotice("");

    try {
      setLoading("Changing password...");

      await api.changePassword({
        current_password: currentPassword,
        new_password: changeNewPassword,
      });

      setCurrentPassword("");
      setChangeNewPassword("");
      setNotice("Password changed.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  function logout() {
    clearToken();
    setTokenState(null);
    setUser(null);
    setSaved([]);
    setPage("home");
    setNotice("Logged out.");
  }

  async function saveAnalysis() {
    if (!analysis) return;

    if (!loggedIn) {
      setNotice("Login to save your result.");
      setPage("account");
      return;
    }

    try {
      setLoading("Saving...");

      await api.saveAnalysis({
        title: jobTitle,
        company,
        final_score: analysis.final_score,
        report_markdown: analysis.report_markdown,
        structured_report: analysis.structured_report,
        job_description: jobDescription,
      });

      await loadSaved();
      setNotice("Saved.");
      setPage("dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function saveFeedback(e) {
    e.preventDefault();

    if (!loggedIn) {
      setPage("account");
      return;
    }

    try {
      setLoading("Saving feedback...");

      await api.saveFeedback({
        ...feedback,
        rating: Number(feedback.rating),
        match_analysis_id: saved[0]?.id || null,
      });

      setNotice("Feedback saved.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function renameSavedAnalysis(item) {
    const newTitle = window.prompt("New title", item.title || "");
    if (newTitle === null) return;

    const newCompany = window.prompt("Company", item.company || "");
    if (newCompany === null) return;

    try {
      setLoading("Updating saved result...");

      await api.updateAnalysis(item.id, {
        title: newTitle,
        company: newCompany,
      });

      await loadSaved();
      setNotice("Updated.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function deleteSavedAnalysis(item) {
    const ok = window.confirm(
      `Delete "${item.title || "Untitled"}"? This cannot be undone.`,
    );

    if (!ok) return;

    try {
      setLoading("Deleting saved result...");

      await api.deleteAnalysis(item.id);

      await loadSaved();
      setNotice("Deleted.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function moveSavedAnalysis(index, direction) {
    const next = [...saved];
    const targetIndex = index + direction;

    if (targetIndex < 0 || targetIndex >= next.length) return;

    const temp = next[index];
    next[index] = next[targetIndex];
    next[targetIndex] = temp;

    setSaved(next);

    try {
      await api.reorderAnalysis(next.map((item) => item.id));
    } catch (err) {
      setError(err.message);
      await loadSaved();
    }
  }

  return (
    <div>
      <header className="nav">
        <button className="brand" onClick={() => setPage("home")}>
          <span>R</span>
          Resumagic
        </button>

        <div>
          <em className={status === "online" ? "ok" : "bad"}>API {status}</em>

          <button onClick={() => setPage("home")}>Home</button>

          <button onClick={() => setPage("account")}>
            {loggedIn ? "Account" : "Login"}
          </button>

          <button onClick={() => setPage("dashboard")}>Dashboard</button>

          {loggedIn && <button onClick={logout}>Logout</button>}
        </div>
      </header>

      {(loading || error || notice) && (
        <section className="status">
          {loading && <p className="load">{loading}</p>}
          {notice && <p className="note">{notice}</p>}
          {error && <p className="err">{error}</p>}
        </section>
      )}

      {page === "home" && (
        <>
          <section className="hero">
            <div>
              <p className="eyebrow">AI Resume Consultant</p>
              <h1>Check your resume match before you apply.</h1>
              <p>
                Upload a resume, paste a job posting, and get an instant score
                and resume advice. No account required for first analysis.
              </p>
            </div>

            <aside>
              Login only when you want to save history and feedback.
            </aside>
          </section>

          <main className="container">
            <section className="card">
              <h2>Free Resume Match Check</h2>

              <form onSubmit={analyze} className="grid">
                <div>
                  <label>Resume</label>
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt,.md"
                    onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
                  />

                  <label>Job title</label>
                  <input
                    value={jobTitle}
                    onChange={(e) => setJobTitle(e.target.value)}
                    placeholder="Backend Developer"
                  />

                  <label>Company</label>
                  <input
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    placeholder="Company"
                  />
                </div>

                <div>
                  <label>Job posting file optional</label>
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt,.md"
                    onChange={(e) => setJobFile(e.target.files?.[0] || null)}
                  />

                  <label>Job description</label>
                  <textarea
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    placeholder="Or paste the full job posting here..."
                  />

                  <button className="primary">Analyze Resume</button>
                </div>
              </form>
            </section>

            {analysis && (
              <section id="result" className="result">
                <div className="score">
                  <small>Match Score</small>
                  <strong>{analysis.final_score}%</strong>
                  <p>{analysis.summary}</p>

                  <button className="primary" onClick={saveAnalysis}>
                    {loggedIn ? "Save result" : "Login to save"}
                  </button>
                </div>

                <div className="report">
                  <h2>AI Report</h2>
                  <pre>{analysis.report_markdown}</pre>
                </div>
              </section>
            )}
          </main>
        </>
      )}

      {page === "account" && (
        <main className="container narrow">
          <section className="card">
            <h2>{loggedIn ? "Account" : "Login / Signup"}</h2>

            {loggedIn ? (
              <>
                <p>
                  Logged in as <b>{user?.email}</b>
                </p>

                <button
                  className="primary"
                  onClick={() => setPage("dashboard")}
                >
                  Dashboard
                </button>

                <hr />

                <h3>Change Password</h3>

                <form onSubmit={changePassword} className="form">
                  <input
                    type="password"
                    placeholder="Current password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                  />

                  <input
                    type="password"
                    placeholder="New password"
                    value={changeNewPassword}
                    onChange={(e) => setChangeNewPassword(e.target.value)}
                  />

                  <button className="primary">Change password</button>
                </form>
              </>
            ) : (
              <>
                <form onSubmit={handleAuth} className="form">
                  <div className="toggle">
                    <button
                      type="button"
                      className={authMode === "login" ? "active" : ""}
                      onClick={() => setAuthMode("login")}
                    >
                      Login
                    </button>

                    <button
                      type="button"
                      className={authMode === "signup" ? "active" : ""}
                      onClick={() => setAuthMode("signup")}
                    >
                      Signup
                    </button>
                  </div>

                  {authMode === "signup" && (
                    <input
                      placeholder="Full name"
                      value={auth.full_name}
                      onChange={(e) =>
                        setAuth({ ...auth, full_name: e.target.value })
                      }
                    />
                  )}

                  <input
                    type="email"
                    placeholder="Email"
                    value={auth.email}
                    onChange={(e) =>
                      setAuth({ ...auth, email: e.target.value })
                    }
                  />

                  <input
                    type="password"
                    placeholder="Password"
                    value={auth.password}
                    onChange={(e) =>
                      setAuth({ ...auth, password: e.target.value })
                    }
                  />

                  <button className="primary">
                    {authMode === "signup" ? "Create account" : "Login"}
                  </button>
                </form>

                <button
                  type="button"
                  className="linkButton"
                  onClick={() => setPage("forgot-password")}
                >
                  Forgot password?
                </button>
              </>
            )}
          </section>
        </main>
      )}

      {page === "forgot-password" && (
        <main className="container narrow">
          <section className="card">
            <h2>Forgot Password</h2>

            <p className="muted">
              Enter your email and we’ll send you a password reset link.
            </p>

            <form onSubmit={requestPasswordReset} className="form">
              <input
                type="email"
                placeholder="Your email"
                value={resetEmail}
                onChange={(e) => setResetEmail(e.target.value)}
              />

              <button className="primary">Send reset link</button>

              <button
                type="button"
                className="linkButton"
                onClick={() => setPage("account")}
              >
                Back to login
              </button>
            </form>
          </section>
        </main>
      )}

      {page === "reset-password" && (
        <main className="container narrow">
          <section className="card">
            <h2>Reset Password</h2>

            <form onSubmit={resetPassword} className="form">
              <input
                type="email"
                placeholder="Email"
                value={resetEmail}
                onChange={(e) => setResetEmail(e.target.value)}
              />

              <input
                placeholder="Reset token"
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
              />

              <input
                type="password"
                placeholder="New password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />

              <button className="primary">Reset password</button>
            </form>
          </section>
        </main>
      )}

      {page === "dashboard" && (
        <main className="container">
          <h2>Your Dashboard</h2>

          {!loggedIn ? (
            <section className="card">
              <p>Login required.</p>

              <button className="primary" onClick={() => setPage("account")}>
                Login / Signup
              </button>
            </section>
          ) : (
            <section className="dash">
              <div className="card">
                <h2>Saved analyses</h2>

                {saved.length ? (
                  saved.map((s, index) => (
                    <div className="saved" key={s.id}>
                      <div>
                        <b>
                          {s.title || "Untitled"}{" "}
                          {s.company ? `@ ${s.company}` : ""}
                        </b>
                        <span>{s.final_score}% match</span>
                      </div>

                      <div className="savedActions">
                        <button
                          type="button"
                          onClick={() => moveSavedAnalysis(index, -1)}
                          disabled={index === 0}
                        >
                          ↑
                        </button>

                        <button
                          type="button"
                          onClick={() => moveSavedAnalysis(index, 1)}
                          disabled={index === saved.length - 1}
                        >
                          ↓
                        </button>

                        <button
                          type="button"
                          onClick={() => renameSavedAnalysis(s)}
                        >
                          Rename
                        </button>

                        <button
                          type="button"
                          className="danger"
                          onClick={() => deleteSavedAnalysis(s)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p>No saved analyses yet.</p>
                )}
              </div>

              <div className="card">
                <h2>Feedback</h2>

                <form onSubmit={saveFeedback} className="form">
                  <label>Rating: {feedback.rating}/5</label>

                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={feedback.rating}
                    onChange={(e) =>
                      setFeedback({ ...feedback, rating: e.target.value })
                    }
                  />

                  <label>
                    <input
                      type="checkbox"
                      checked={feedback.applied}
                      onChange={(e) =>
                        setFeedback({ ...feedback, applied: e.target.checked })
                      }
                    />{" "}
                    Applied
                  </label>

                  <label>
                    <input
                      type="checkbox"
                      checked={feedback.interview_received}
                      onChange={(e) =>
                        setFeedback({
                          ...feedback,
                          interview_received: e.target.checked,
                        })
                      }
                    />{" "}
                    Interview received
                  </label>

                  <textarea
                    placeholder="Notes"
                    value={feedback.user_notes}
                    onChange={(e) =>
                      setFeedback({ ...feedback, user_notes: e.target.value })
                    }
                  />

                  <button className="primary">Save feedback</button>
                </form>
              </div>
            </section>
          )}
        </main>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);