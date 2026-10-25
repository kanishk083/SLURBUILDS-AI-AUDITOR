"use client";
import { useState, useEffect, useCallback, useRef } from "react";
import {
  ArrowRight,
  BookOpen,
  Check,
  CheckCheck,
  ChevronDown,
  ChevronRight,
  Clock3,
  FileText,
  FlaskConical,
  FolderOpen,
  History,
  Layers3,
  Loader2,
  LogOut,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
  Upload,
  X,
  AlertCircle,
  RotateCcw,
  ExternalLink,
} from "lucide-react";

type KB = { id: string; name: string };
type Doc = {
  id: string;
  name: string;
  status: string;
  error?: string;
  chunk_count: number;
};
type Evidence = {
  id: string;
  document_id: string;
  document_name: string;
  text: string;
  page: number | null;
  line_start: number;
  line_end: number;
  score: number;
  relevance?: number;
  accepted?: boolean;
  relation?: string;
  quote?: string;
  strip_index?: number;
  model_scores?: Record<string, number>;
};
type Step = {
  step: string;
  round: number;
  query?: string;
  from?: string;
  to?: string;
  reason?: string;
  candidate_count?: number;
  accepted_count?: number;
  candidates?: Evidence[];
  text?: string;
};
type Claim = {
  id: string;
  text: string;
  verdict: string;
  explanation: string;
  citations: Evidence[];
  trace: Step[];
  stop_reason: string;
};
type AuditResult = {
  claims: Claim[];
  counts: Record<string, number>;
  mode: string;
  provider: string;
  latency_ms: number;
  extraction: string;
  model: string;
  verification_pairs: number;
  scope_note: string;
  limitations: string[];
};
type Audit = {
  id: string;
  question: string;
  answer: string;
  mode: string;
  status: string;
  error?: string;
  result?: AuditResult;
  counts?: Record<string, number>;
  latency_ms?: number;
  created_at: string;
};
type Config = {
  demo_enabled: boolean;
  hosted_configured: boolean;
  embedding_model: string;
  nli_model: string;
};
type EvalRun = {
  id: string;
  status: string;
  result?: {
    notice?: string;
    error?: string;
    modes?: Record<
      string,
      {
        case_count: number;
        fixture_agreement: number;
        macro_f1: number;
        p95_ms: number;
      }
    >;
  };
};

const labels: Record<string, string> = {
  supported: "Supported",
  contradicted: "Contradicted",
  insufficient_evidence: "Insufficient evidence",
};
const modeOptions = [
  ["corrective", "Corrective", "Evaluate evidence and retry weak retrieval."],
  [
    "baseline",
    "Fixed hybrid baseline",
    "Hybrid search without retrieval filtering or evidence refinement.",
  ],
  ["filter", "Filter only", "Evaluate hybrid results without correction."],
  [
    "contextual",
    "Context-enriched",
    "Index document title and heading context.",
  ],
  ["parent_window", "Context window", "Include neighboring source passages."],
  ["multi_query", "Multi-query", "Fuse original and expanded query results."],
  [
    "hyde",
    "Hypothetical search",
    "Local generated search aid; never source evidence.",
  ],
  [
    "adaptive",
    "Adaptive",
    "Route exact-value queries to lexical search, then hybrid recovery.",
  ],
  [
    "agentic",
    "Read-only agent",
    "A small local planner chooses bounded, authorized retrieval tools.",
  ],
];
async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch("/api/v1" + path, {
    credentials: "include",
    ...options,
    headers:
      options.body instanceof FormData
        ? options.headers
        : { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : "Request failed. Check your input and retry.",
    );
  }
  return response.json();
}
const phaseNotes = [
  [
    "0",
    "Evidence foundations",
    "AI answer ko claims mein split karte hain. Source same claim ko support kare, opposite fact bole, ya enough evidence na ho — yeh teen alag results hain.",
  ],
  [
    "1",
    "Inspectable retrieval",
    "Har chunk original document aur line/page ke saath store hota hai. Relevant passage ka source trace kar paana retrieval score se zyada useful debugging signal hai.",
  ],
  [
    "2",
    "Reliable ingestion",
    "Upload pehle private storage aur database mein persist hota hai. Worker pending records recover karta hai; duplicate jobs same active chunks dobara create nahi karte.",
  ],
  [
    "3",
    "Hybrid search",
    "Lexical search exact terms pakadti hai. Dense search paraphrases la sakti hai. RRF dono ranked lists merge karta hai; raw scores ko blindly add nahi karte.",
  ],
  [
    "4",
    "Claim verification",
    "Local mode sentence boundaries se candidate claims nikalta hai; NLI source/claim pair ko score karta hai. Missing evidence ko false label nahi karte.",
  ],
  [
    "5",
    "Corrective retrieval",
    "Weak evidence par focused query rewrite aur bounded re-search hota hai. Maximum rounds aur deadline loops ko control karte hain.",
  ],
  [
    "6",
    "Audit workspace",
    "Har verdict source quote tak navigate hota hai. Trace mein original/revised query aur rejected evidence inspect kar sakte ho.",
  ],
  [
    "7",
    "Evaluation and reliability",
    "Retrieval, extraction aur verification errors separately measure karo. Small synthetic fixtures ko real-world accuracy proof mat banao.",
  ],
  [
    "8",
    "Context and query labs",
    "Context enrichment, parent windows, multi-query aur HyDE same corpus par compare karo. Generated search aids original evidence nahi hote.",
  ],
  [
    "9",
    "Representation labs",
    "Exact vs HNSW recall alag measure karo. Late pooling aur MaxSim mechanism labs trained long-context/ColBERT reproductions nahi hain.",
  ],
  [
    "10",
    "Advanced research",
    "Hierarchy, graph aur agentic tools additional hypotheses hain. Har derived artifact ka original source aur authorization preserve rehna chahiye.",
  ],
  [
    "11",
    "Interview walkthrough",
    "Ek claim ko input span se source, evaluator, correction aur final verdict tak trace karo. Improvement aur unresolved failure dono explain karo.",
  ],
];
export default function Home() {
  const [config, setConfig] = useState<Config | null>(null),
    [account, setAccount] = useState<{ email: string } | null>(null);
  const [boot, setBoot] = useState(true),
    [tab, setTab] = useState("workspace"),
    [authTab, setAuthTab] = useState("demo");
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [authBusy, setAuthBusy] = useState(false);
  const [kbs, setKbs] = useState<KB[]>([]),
    [kb, setKb] = useState(""),
    [docs, setDocs] = useState<Doc[]>([]);
  const [newLibraryName, setNewLibraryName] = useState(""),
    [showLibraryForm, setShowLibraryForm] = useState(false);
  const [question, setQuestion] = useState(""),
    [answer, setAnswer] = useState(""),
    [mode, setMode] = useState("corrective");
  const [provider, setProvider] = useState("local_nli"),
    [audit, setAudit] = useState<Audit | null>(null),
    [history, setHistory] = useState<Audit[]>([]);
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [uploading, setUploading] = useState(false),
    [filter, setFilter] = useState("all");
  const [expanded, setExpanded] = useState<string | null>(null),
    [source, setSource] = useState<Evidence | null>(null),
    [sourceText, setSourceText] = useState("");
  const [metrics, setMetrics] = useState<{
    completed_audits: number;
    failed_audits: number;
    p50_ms: number | null;
    p95_ms: number | null;
    sample_count: number;
  } | null>(null);
  const [evalRun, setEvalRun] = useState<EvalRun | null>(null),
    [evalBusy, setEvalBusy] = useState(false);
  const [labKind, setLabKind] = useState("late_interaction"),
    [labBusy, setLabBusy] = useState(false),
    [labResult, setLabResult] = useState<unknown>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const notify = (e: unknown) =>
    setError(e instanceof Error ? e.message : String(e));
  const loadAccount = useCallback(async () => {
    const me = await api<{ email: string }>("/auth/me");
    setAccount(me);
    const bases = await api<KB[]>("/knowledge-bases");
    setKbs(bases);
    setKb(bases[0]?.id || "");
  }, []);
  useEffect(() => {
    Promise.all([
      api<Config>("/config").then(setConfig),
      loadAccount().catch(() => {}),
    ])
      .catch(notify)
      .finally(() => setBoot(false));
  }, [loadAccount]);
  const refresh = useCallback(async () => {
    if (!kb) return;
    const [d, h, m] = await Promise.all([
      api<Doc[]>("/documents?kb_id=" + kb),
      api<Audit[]>("/audits?kb_id=" + kb),
      api<typeof metrics>("/metrics"),
    ]);
    setDocs(d);
    setHistory(h);
    setMetrics(m);
  }, [kb]);
  useEffect(() => {
    if (!account || !kb) return;
    refresh().catch(notify);
    const timer = setInterval(() => refresh().catch(() => {}), 3000);
    return () => clearInterval(timer);
  }, [account, kb, refresh]);
  useEffect(() => {
    if (!audit || !["pending", "running"].includes(audit.status)) return;
    const timer = setInterval(
      () =>
        api<Audit>("/audits/" + audit.id)
          .then((a) => {
            setAudit(a);
            if (a.status === "completed")
              setExpanded(a.result?.claims[0]?.id || null);
          })
          .catch(notify),
      1500,
    );
    return () => clearInterval(timer);
  }, [audit?.id, audit?.status]);
  useEffect(() => {
    if (!evalRun || !["pending", "running"].includes(evalRun.status)) return;
    const timer = setInterval(
      () =>
        api<EvalRun>("/evaluations/" + evalRun.id)
          .then(setEvalRun)
          .catch(notify),
      2000,
    );
    return () => clearInterval(timer);
  }, [evalRun?.id, evalRun?.status]);
  useEffect(() => {
    if (!source) return;
    const listener = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSource(null);
    };
    window.addEventListener("keydown", listener);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", listener);
      document.body.style.overflow = previous;
    };
  }, [source]);
  async function evaluateFixture() {
    setEvalBusy(true);
    setError("");
    try {
      setEvalRun(
        await api<EvalRun>("/evaluations/run", {
          method: "POST",
          body: JSON.stringify({ kb_id: kb, split: "development" }),
        }),
      );
    } catch (e) {
      notify(e);
    } finally {
      setEvalBusy(false);
    }
  }
  async function runLab() {
    setLabBusy(true);
    setError("");
    try {
      setLabResult(
        await api("/labs/run", {
          method: "POST",
          body: JSON.stringify({
            kb_id: kb,
            kind: labKind,
            query:
              answer.split("\n")[0] ||
              question ||
              "What evidence is available?",
          }),
        }),
      );
    } catch (e) {
      notify(e);
    } finally {
      setLabBusy(false);
    }
  }
  async function authenticate(demo = false) {
    setAuthBusy(true);
    setError("");
    try {
      await api(
        "/auth/" +
          (demo ? "guest" : authTab === "register" ? "register" : "login"),
        {
          method: "POST",
          body: demo ? undefined : JSON.stringify({ email, password }),
        },
      );
      await loadAccount();
    } catch (e) {
      notify(e);
    } finally {
      setAuthBusy(false);
    }
  }
  async function seed() {
    setBusy(true);
    setError("");
    try {
      const sample = await api<{ question: string; answer: string }>(
        "/demo/seed?kb_id=" + kb,
        { method: "POST" },
      );
      setQuestion(sample.question);
      setAnswer(sample.answer);
      setAudit(null);
      setTab("workspace");
      await refresh();
    } catch (e) {
      notify(e);
    } finally {
      setBusy(false);
    }
  }
  async function upload(files: FileList | null) {
    if (!files) return;
    setUploading(true);
    setError("");
    try {
      for (const file of Array.from(files)) {
        const form = new FormData();
        form.append("kb_id", kb);
        form.append("file", file);
        await api("/documents", { method: "POST", body: form });
      }
      await refresh();
    } catch (e) {
      notify(e);
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }
  async function submit(selectedMode = mode) {
    setBusy(true);
    setError("");
    setFilter("all");
    try {
      const item = await api<Audit>("/audits", {
        method: "POST",
        body: JSON.stringify({
          kb_id: kb,
          question,
          answer,
          mode: selectedMode,
          provider,
        }),
      });
      setAudit(item);
      setTab("workspace");
      await refresh();
    } catch (e) {
      notify(e);
    } finally {
      setBusy(false);
    }
  }
  async function createLibrary(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const created = await api<KB>("/knowledge-bases", {
        method: "POST",
        body: JSON.stringify({ name: newLibraryName.trim() }),
      });
      setKbs((current) => [...current, created]);
      setKb(created.id);
      setDocs([]);
      setAudit(null);
      setEvalRun(null);
      setLabResult(null);
      setShowLibraryForm(false);
      setNewLibraryName("");
    } catch (e) {
      notify(e);
    } finally {
      setBusy(false);
    }
  }
  async function remove(doc: Doc) {
    setError("");
    try {
      await api("/documents/" + doc.id, { method: "DELETE" });
      setAudit(null);
      await refresh();
    } catch (e) {
      notify(e);
    }
  }
  async function showSource(e: Evidence) {
    setSource(e);
    setSourceText("");
    try {
      const body = await api<{ passages: Evidence[] }>(
        "/documents/" + e.document_id + "/source",
      );
      setSourceText(
        body.passages
          .map(
            (p) =>
              (p.page ? "Page " + p.page + ", " : "") +
              "lines " +
              p.line_start +
              "–" +
              p.line_end +
              "\n" +
              p.text,
          )
          .join("\n\n"),
      );
    } catch (err) {
      notify(err);
      setSource(null);
    }
  }
  const indexed = docs.filter((d) => d.status === "indexed").length,
    working = docs.some((d) => ["pending", "indexing"].includes(d.status));
  const running = !!audit && ["pending", "running"].includes(audit.status),
    result = audit?.status === "completed" ? audit.result : undefined;
  const visible =
    result?.claims.filter((c) => filter === "all" || c.verdict === filter) ||
    [];
  if (boot)
    return (
      <main className="boot">
        <div className="brand-mark">
          <ShieldCheck size={28} />
        </div>
        <Loader2 className="spin" />
        <p>Opening your workspace…</p>
      </main>
    );
  if (!account)
    return (
      <main className="welcome">
        <div className="welcome-art">
          <div className="brand">
            <div className="brand-mark">
              <ShieldCheck size={23} />
            </div>
            AI Auditor
          </div>
          <div className="intro">
            <span className="tiny-tag">An evidence-first workspace</span>
            <h1>
              Every claim
              <br />
              needs evidence.
            </h1>
            <p>
              Bring your reference documents and an AI answer. See what holds
              up, what conflicts, and what the sources don’t establish.
            </p>
            <div className="sample-claim">
              <span className="verdict supported">
                <CheckCheck size={14} />
                Supported
              </span>
              <p>“The source supports this claim.”</p>
              <div>
                <FileText size={15} />
                Reference document, lines 7–8
              </div>
            </div>
            <div className="intro-foot">
              <Search size={18} />
              Retrieve evidence
              <ChevronRight size={16} />
              <Layers3 size={18} />
              Check each claim
              <ChevronRight size={16} />
              <ShieldCheck size={18} />
              Follow the source
            </div>
          </div>
        </div>
        <section className="welcome-form">
          <div className="form-wrap">
            <h2>Your evidence. Your verdicts.</h2>
            <p className="muted">A clear audit trail from answer to source.</p>
            <div className="segmented">
              {config?.demo_enabled && (
                <button
                  className={authTab === "demo" ? "selected" : ""}
                  onClick={() => setAuthTab("demo")}
                >
                  Try demo
                </button>
              )}
              <button
                className={authTab === "login" ? "selected" : ""}
                onClick={() => setAuthTab("login")}
              >
                Sign in
              </button>
              <button
                className={authTab === "register" ? "selected" : ""}
                onClick={() => setAuthTab("register")}
              >
                Create account
              </button>
            </div>
            {error && (
              <div role="alert" className="error">
                <AlertCircle size={18} />
                {error}
              </div>
            )}
            {authTab === "demo" && config?.demo_enabled ? (
              <>
                <div className="demo-note">
                  <FolderOpen size={26} />
                  <h3>Start a private demo</h3>
                  <p>
                    Use sample documents or upload your own. Each session has
                    its own reference library.
                  </p>
                </div>
                <button
                  className="primary wide"
                  disabled={authBusy}
                  onClick={() => authenticate(true)}
                >
                  {authBusy ? (
                    <Loader2 className="spin" size={18} />
                  ) : (
                    <ArrowRight size={18} />
                  )}
                  Open workspace
                </button>
                <small>
                  Runs with local AI models. Model scores are not guarantees of
                  truth.
                </small>
              </>
            ) : (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  authenticate();
                }}
              >
                <label>
                  Email
                  <input
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </label>
                <label>
                  Password
                  <input
                    type="password"
                    minLength={10}
                    maxLength={128}
                    autoComplete={
                      authTab === "register"
                        ? "new-password"
                        : "current-password"
                    }
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </label>
                <button className="primary wide" disabled={authBusy}>
                  {authBusy ? <Loader2 className="spin" size={18} /> : null}
                  {authTab === "register" ? "Create account" : "Sign in"}
                </button>
                <small>Use at least 10 characters for your password.</small>
              </form>
            )}
          </div>
          <footer>AI Auditor · Built to make AI answers inspectable.</footer>
        </section>
      </main>
    );
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <ShieldCheck size={22} />
          </div>
          AI Auditor
        </div>
        <div className="workspace-select">
          <span>Reference library</span>
          <select
            aria-label="Reference library"
            value={kb}
            onChange={(e) => {
              setKb(e.target.value);
              setAudit(null);
              setDocs([]);
              setEvalRun(null);
              setLabResult(null);
            }}
          >
            {kbs.map((x) => (
              <option key={x.id} value={x.id}>
                {x.name}
              </option>
            ))}
          </select>
          <button
            className="new-library"
            onClick={() => setShowLibraryForm(!showLibraryForm)}
          >
            <Plus size={12} />
            New library
          </button>
          {showLibraryForm && (
            <form className="library-form" onSubmit={createLibrary}>
              <label>
                Library name
                <input
                  aria-label="Library name"
                  value={newLibraryName}
                  onChange={(e) => setNewLibraryName(e.target.value)}
                  maxLength={120}
                  required
                />
              </label>
              <button
                className="primary"
                disabled={busy || !newLibraryName.trim()}
              >
                Create library
              </button>
              <button
                type="button"
                className="icon-button"
                aria-label="Cancel new library"
                onClick={() => setShowLibraryForm(false)}
              >
                <X size={15} />
              </button>
            </form>
          )}
        </div>
        <nav>
          {[
            ["workspace", "Audit workspace", Search],
            ["history", "Audit history", History],
            ["experiments", "Compare methods", FlaskConical],
            ["learning", "Learning notes", BookOpen],
          ].map(([id, name, Icon]) => {
            const I = Icon as typeof Search;
            return (
              <button
                key={id as string}
                className={tab === id ? "active" : ""}
                onClick={() => setTab(id as string)}
              >
                <I size={18} />
                {name as string}
              </button>
            );
          })}
        </nav>
        <div className="library-heading">
          <span>Documents</span>
          <span className="count">{docs.length}</span>
        </div>
        <div className="document-list">
          {docs.length === 0 ? (
            <div className="empty-doc">
              <FileText size={25} />
              <p>Your sources will live here.</p>
            </div>
          ) : (
            docs.map((d) => (
              <div className="document" key={d.id}>
                <FileText size={18} />
                <div>
                  <span title={d.name}>{d.name}</span>
                  <small
                    className={
                      d.status === "failed" || d.status === "needs_ocr"
                        ? "bad-text"
                        : ""
                    }
                  >
                    {d.status === "indexed"
                      ? d.chunk_count + " passages"
                      : d.status.replace("_", " ")}
                  </small>
                  {d.error && <small title={d.error}>{d.error}</small>}
                </div>
                <button
                  aria-label={"Delete " + d.name}
                  className="icon-button delete"
                  onClick={() => remove(d)}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))
          )}
        </div>
        <input
          ref={inputRef}
          type="file"
          hidden
          multiple
          accept=".pdf,.txt,.md,.markdown"
          onChange={(e) => upload(e.target.files)}
        />
        <button
          className="upload-button"
          disabled={uploading}
          onClick={() => inputRef.current?.click()}
        >
          {uploading ? (
            <Loader2 className="spin" size={17} />
          ) : (
            <Upload size={17} />
          )}
          Upload documents
        </button>
        <small className="upload-hint">
          PDF, TXT or Markdown · up to 20 MB
        </small>
        <div className="sidebar-footer">
          <div className="avatar">
            {account.email.startsWith("guest-")
              ? "D"
              : account.email[0].toUpperCase()}
          </div>
          <div>
            <strong>
              {account.email.startsWith("guest-")
                ? "Private demo"
                : account.email.split("@")[0]}
            </strong>
            <small>Isolated reference library</small>
          </div>
          <button
            className="icon-button"
            aria-label="Sign out"
            onClick={() =>
              api("/auth/logout", { method: "POST" }).then(() => {
                setAccount(null);
                setDocs([]);
                setAudit(null);
              })
            }
          >
            <LogOut size={17} />
          </button>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <span>
            {tab === "workspace"
              ? "Audit workspace"
              : tab === "history"
                ? "Audit history"
                : tab === "experiments"
                  ? "Compare methods"
                  : "Learning notes"}
          </span>
          <div>
            <span className={"status-dot " + (working ? "amber" : "")} />
            {working
              ? "Indexing documents"
              : indexed
                ? indexed + " sources ready"
                : "Add your references"}
            <span className="local-badge">
              {provider === "hosted" ? "Hosted AI" : "Local AI"}
            </span>
          </div>
        </header>
        {error && (
          <div role="alert" className="error banner">
            <AlertCircle size={18} />
            {error}
            <button aria-label="Dismiss error" onClick={() => setError("")}>
              <X size={16} />
            </button>
          </div>
        )}
        {tab === "workspace" && (
          <div className="workspace-content">
            <div className="page-intro">
              <div>
                <h1>Follow the evidence.</h1>
                <p>Review an AI answer against the documents you trust.</p>
              </div>
              {config?.demo_enabled && (
                <button className="secondary" disabled={busy} onClick={seed}>
                  <Sparkles size={16} />
                  Load sample
                </button>
              )}
            </div>
            <div className={"audit-grid " + (result ? "has-report" : "")}>
              <section className="editor-panel">
                <div className="panel-heading">
                  <span className="step-number">1</span>
                  <div>
                    <h2>The answer to review</h2>
                    <p>
                      Keep the original wording so every claim is traceable.
                    </p>
                  </div>
                </div>
                <label>
                  Original question <span className="optional">optional</span>
                  <textarea
                    className="question-input"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="What was the AI asked?"
                    maxLength={2000}
                  />
                </label>
                <label>
                  AI-generated answer
                  <textarea
                    className="answer-input"
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                    placeholder="Paste the answer you want to audit…"
                    maxLength={12000}
                  />
                </label>
                <div className="input-meta">
                  <span>
                    {answer.length.toLocaleString()} / 12,000 characters
                  </span>
                  <span>Up to 20 candidate claims</span>
                </div>
                <div className="method-row">
                  <label>
                    Retrieval method
                    <select
                      value={mode}
                      onChange={(e) => setMode(e.target.value)}
                    >
                      {modeOptions.map(([v, n]) => (
                        <option key={v} value={v}>
                          {n}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Verifier
                    <select
                      value={provider}
                      onChange={(e) => setProvider(e.target.value)}
                    >
                      <option value="local_nli">Local NLI</option>
                      {config?.hosted_configured && (
                        <option value="hosted">Hosted model</option>
                      )}
                    </select>
                  </label>
                </div>
                <p className="method-help">
                  {modeOptions.find((m) => m[0] === mode)?.[2]}
                </p>
                <button
                  className="primary audit-button"
                  disabled={busy || running || !answer.trim() || !indexed}
                  onClick={() => submit()}
                >
                  {running ? (
                    <Loader2 className="spin" size={18} />
                  ) : (
                    <ShieldCheck size={18} />
                  )}{" "}
                  {running ? "Auditing the evidence…" : "Audit answer"}
                  {!running && <ArrowRight size={18} />}
                </button>
                {!indexed && (
                  <p className="helper">
                    {working
                      ? "Your documents are being indexed. Auditing will be available when they are ready."
                      : "Upload reference documents or load the sample to begin."}
                  </p>
                )}
              </section>
              <section className="report-panel">
                <div className="panel-heading">
                  <span className="step-number">2</span>
                  <div>
                    <h2>The evidence report</h2>
                    <p>Source-grounded verdicts, one claim at a time.</p>
                  </div>
                  {result && (
                    <span className="duration">
                      <Clock3 size={13} />
                      {(result.latency_ms / 1000).toFixed(1)}s
                    </span>
                  )}
                </div>
                {!audit ? (
                  <div className="report-empty">
                    <div className="evidence-illustration">
                      <FileText size={42} />
                      <div>
                        <Check size={14} />
                      </div>
                    </div>
                    <h3>A verdict you can inspect.</h3>
                    <p>
                      Your report will connect each claim to supporting or
                      conflicting source passages.
                    </p>
                    <div className="verdict-key">
                      <span>
                        <i className="dot green" />
                        Supported
                      </span>
                      <span>
                        <i className="dot red" />
                        Contradicted
                      </span>
                      <span>
                        <i className="dot orange" />
                        Insufficient evidence
                      </span>
                    </div>
                  </div>
                ) : running ? (
                  <div className="report-empty">
                    <Loader2 size={38} className="spin" />
                    <h3>
                      {audit.status === "pending"
                        ? "Waiting for the audit worker…"
                        : "Following the sources…"}
                    </h3>
                    <p>
                      Retrieving passages, checking evidence and correcting weak
                      searches. The first run also loads the local verifier.
                    </p>
                    <span className="soft-badge">
                      {modeOptions.find((m) => m[0] === audit.mode)?.[1] ||
                        audit.mode}
                    </span>
                  </div>
                ) : audit.status !== "completed" ? (
                  <div className="report-empty">
                    <AlertCircle size={35} />
                    <h3>
                      {audit.status === "invalidated"
                        ? "Reference library changed"
                        : "Audit needs attention"}
                    </h3>
                    <p>{audit.error || "The report could not be completed."}</p>
                    <button
                      className="secondary"
                      onClick={() => {
                        setQuestion(audit.question);
                        setAnswer(audit.answer);
                        setAudit(null);
                      }}
                    >
                      Review input
                    </button>
                  </div>
                ) : (
                  result && (
                    <>
                      <div className="report-summary">
                        {[
                          "supported",
                          "contradicted",
                          "insufficient_evidence",
                        ].map((k) => (
                          <button
                            key={k}
                            className={filter === k ? "selected" : ""}
                            onClick={() => setFilter(filter === k ? "all" : k)}
                          >
                            <span className={"summary-number " + k}>
                              {result.counts[k]}
                            </span>
                            <span>{labels[k]}</span>
                          </button>
                        ))}
                      </div>
                      <div className="claim-list">
                        {visible.map((c) => (
                          <article className={"claim " + c.verdict} key={c.id}>
                            <button
                              className="claim-header"
                              onClick={() =>
                                setExpanded(expanded === c.id ? null : c.id)
                              }
                              aria-expanded={expanded === c.id}
                            >
                              <span className="claim-id">{c.id}</span>
                              <div>
                                <p>{c.text}</p>
                                <span className={"verdict " + c.verdict}>
                                  {c.verdict === "supported" ? (
                                    <CheckCheck size={13} />
                                  ) : c.verdict === "contradicted" ? (
                                    <X size={13} />
                                  ) : (
                                    <Search size={13} />
                                  )}{" "}
                                  {labels[c.verdict]}
                                </span>
                              </div>
                              {expanded === c.id ? (
                                <ChevronDown size={18} />
                              ) : (
                                <ChevronRight size={18} />
                              )}
                            </button>
                            {expanded === c.id && (
                              <div className="claim-detail">
                                <p>{c.explanation}</p>
                                {c.citations.map((e) => (
                                  <button
                                    key={e.id + e.relation + e.strip_index}
                                    className="citation"
                                    onClick={() => showSource(e)}
                                  >
                                    <div>
                                      <FileText size={14} />
                                      <strong>{e.document_name}</strong>
                                      <ExternalLink size={12} />
                                    </div>
                                    <blockquote>{e.quote || e.text}</blockquote>
                                    <span>
                                      {e.page ? "Page " + e.page + " · " : ""}
                                      Lines {e.line_start}–{e.line_end}
                                    </span>
                                  </button>
                                ))}
                                <details className="trace">
                                  <summary>
                                    Inspect retrieval trail{" "}
                                    <span>
                                      {
                                        c.trace.filter(
                                          (s) => s.step === "evaluate",
                                        ).length
                                      }{" "}
                                      search rounds
                                    </span>
                                  </summary>
                                  {c.trace.map((s, i) => (
                                    <div className="trace-step" key={i}>
                                      <span>
                                        {s.step === "evaluate"
                                          ? "Evidence check"
                                          : s.step === "rewrite"
                                            ? "Query correction"
                                            : s.step.replaceAll("_", " ")}
                                      </span>
                                      {s.query && <code>{s.query}</code>}
                                      {s.to && <code>{s.to}</code>}
                                      {s.text && <p>{s.text}</p>}
                                      {s.candidates && (
                                        <>
                                          <small>
                                            {s.accepted_count} accepted of{" "}
                                            {s.candidate_count} candidates
                                          </small>
                                          {s.candidates.map((e) => (
                                            <button
                                              className="trace-candidate"
                                              key={e.id + String(e.strip_index)}
                                              onClick={() => showSource(e)}
                                            >
                                              <span>
                                                {e.accepted
                                                  ? "Retained"
                                                  : "Filtered"}
                                              </span>
                                              {e.document_name}
                                              <small>
                                                {e.relation || "not verified"}
                                              </small>
                                            </button>
                                          ))}
                                        </>
                                      )}
                                    </div>
                                  ))}
                                  <p className="stop-reason">
                                    Stopped:{" "}
                                    {c.stop_reason.replaceAll("_", " ")}
                                  </p>
                                </details>
                              </div>
                            )}
                          </article>
                        ))}
                      </div>
                      <div className="report-footnote">
                        <ShieldCheck size={15} />
                        <p>
                          Verdicts apply to these sources. Missing evidence does
                          not prove a claim false. Local extraction uses
                          sentence boundaries.
                        </p>
                      </div>
                    </>
                  )
                )}
              </section>
            </div>
          </div>
        )}
        {tab === "history" && (
          <section className="single-page">
            <h1>Your audit history</h1>
            <p className="muted">
              Completed reports and runs that need attention.
            </p>
            {history.length === 0 ? (
              <div className="empty-state">
                <History size={32} />
                <h3>No audits yet</h3>
                <p>
                  Review an answer in the audit workspace to create your first
                  report.
                </p>
              </div>
            ) : (
              <div className="history-list">
                {history.map((a) => (
                  <button
                    key={a.id}
                    onClick={() =>
                      api<Audit>("/audits/" + a.id).then((item) => {
                        setAudit(item);
                        setQuestion(item.question);
                        setAnswer(item.answer);
                        setTab("workspace");
                      })
                    }
                  >
                    <div className="history-icon">
                      <FileText size={20} />
                    </div>
                    <div>
                      <strong>{a.question || a.answer.slice(0, 90)}</strong>
                      <small>
                        {new Date(a.created_at).toLocaleString()} · {a.mode}
                      </small>
                    </div>
                    <span className={"history-status " + a.status}>
                      {a.status}
                    </span>
                    <ChevronRight size={18} />
                  </button>
                ))}
              </div>
            )}
          </section>
        )}
        {tab === "experiments" && (
          <section className="single-page">
            <div className="page-intro">
              <div>
                <h1>Make the comparison.</h1>
                <p>Run the same answer against the same reference library.</p>
              </div>
            </div>
            <div className="experiment-notice">
              <FlaskConical size={22} />
              <p>
                Baseline, filtering and corrective retrieval isolate different
                parts of the pipeline. Use independently reviewed labels to
                measure quality; verdict agreement is not accuracy.
              </p>
            </div>
            <div className="experiment-grid">
              {modeOptions.map(([id, name, description]) => (
                <article key={id}>
                  <FlaskConical size={21} />
                  <h3>{name}</h3>
                  <p>{description}</p>
                  <button
                    className="secondary"
                    disabled={!answer.trim() || !indexed || busy || running}
                    onClick={() => submit(id)}
                  >
                    Run this method
                    <ArrowRight size={15} />
                  </button>
                </article>
              ))}
            </div>
            {!answer.trim() && (
              <p className="helper">
                Enter an AI answer in the workspace first, or load the sample
                documents.
              </p>
            )}
            <section className="research-panel">
              <div>
                <h2>Reproducible fixture comparison</h2>
                <p>
                  Load the three sample documents first. Compare 16 development
                  cases across baseline, filter-only and corrective retrieval.
                  This measures agreement with assistant-authored synthetic
                  labels.
                </p>
              </div>
              <button
                className="secondary"
                disabled={
                  !indexed ||
                  evalBusy ||
                  (!!evalRun && ["pending", "running"].includes(evalRun.status))
                }
                onClick={evaluateFixture}
              >
                {evalBusy ||
                (evalRun && ["pending", "running"].includes(evalRun.status)) ? (
                  <Loader2 size={15} className="spin" />
                ) : (
                  <FlaskConical size={15} />
                )}
                Run fixture evaluation
              </button>
              {evalRun && ["pending", "running"].includes(evalRun.status) && (
                <p className="helper">
                  Evaluation is {evalRun.status}. Keep this workspace open to
                  see the results.
                </p>
              )}
              {evalRun?.status === "failed" && (
                <p className="bad-text">{evalRun.result?.error}</p>
              )}
              {evalRun?.status === "completed" && evalRun.result?.modes && (
                <>
                  <div className="table-scroll">
                    <table className="evaluation-table">
                      <thead>
                        <tr>
                          <th>Method</th>
                          <th>Cases</th>
                          <th>Fixture agreement</th>
                          <th>Macro F1</th>
                          <th>P95</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(evalRun.result.modes).map(
                          ([name, r]) => (
                            <tr key={name}>
                              <td>{name}</td>
                              <td>{r.case_count}</td>
                              <td>{(r.fixture_agreement * 100).toFixed(1)}%</td>
                              <td>{r.macro_f1.toFixed(3)}</td>
                              <td>{r.p95_ms.toFixed(0)} ms</td>
                            </tr>
                          ),
                        )}
                      </tbody>
                    </table>
                  </div>
                  <small>{evalRun.result.notice}</small>
                </>
              )}
            </section>
            <section className="research-panel">
              <h2>Representation and structure labs</h2>
              <p>
                Small executable mechanism experiments over your own authorized
                source passages. These are precisely labeled prototypes, not
                full paper reproductions.
              </p>
              <div className="lab-controls">
                <select
                  aria-label="Research lab"
                  value={labKind}
                  onChange={(e) => setLabKind(e.target.value)}
                >
                  <option value="late_interaction">Token-level MaxSim</option>
                  <option value="late_pooling">
                    Context-window late pooling
                  </option>
                  <option value="hierarchy">Cluster hierarchy</option>
                  <option value="graph">Entity co-occurrence graph</option>
                  <option value="hnsw">Exact vs indexed retrieval</option>
                </select>
                <button
                  className="secondary"
                  disabled={!indexed || labBusy}
                  onClick={runLab}
                >
                  {labBusy ? (
                    <Loader2 className="spin" size={15} />
                  ) : (
                    <FlaskConical size={15} />
                  )}
                  Run lab
                </button>
              </div>
              {labResult !== null && (
                <details className="lab-result" open>
                  <summary>Inspect experiment output</summary>
                  <pre>{JSON.stringify(labResult, null, 2)}</pre>
                </details>
              )}
            </section>
            <h2 className="section-title">Observed service metrics</h2>
            <div className="metrics-grid">
              {[
                ["Completed", metrics?.completed_audits ?? 0],
                ["Failed", metrics?.failed_audits ?? 0],
                [
                  "P50 latency",
                  metrics?.p50_ms == null
                    ? "—"
                    : (metrics.p50_ms / 1000).toFixed(1) + "s",
                ],
                [
                  "P95 latency",
                  metrics?.p95_ms == null
                    ? "—"
                    : (metrics.p95_ms / 1000).toFixed(1) + "s",
                ],
              ].map(([name, value]) => (
                <div key={name}>
                  <span>{name}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
            <small>
              Based on {metrics?.sample_count ?? 0} completed audits in your
              account. Local compute cost is not estimated.
            </small>
          </section>
        )}
        {tab === "learning" && (
          <section className="single-page learning">
            <h1>Understand what you built.</h1>
            <p className="muted">
              Hinglish notes for a source-to-verdict walkthrough.
            </p>
            <div className="learning-list">
              {phaseNotes.map(([id, title, note]) => (
                <details key={id} open={id === "0"}>
                  <summary>
                    <span className="step-number">{id}</span>
                    <strong>{title}</strong>
                    <ChevronDown size={17} />
                  </summary>
                  <p>{note}</p>
                </details>
              ))}
            </div>
            <div className="learning-callout">
              <BookOpen size={23} />
              <p>
                Interview mein ek actual failure trace karo: source mila tha ya
                miss hua, evaluator ne kya retain kiya, correction kyun hui aur
                verdict kis evidence se aaya?
              </p>
            </div>
          </section>
        )}
        <footer className="main-footer">
          <span>
            <ShieldCheck size={14} />
            AI Auditor
          </span>
          <span>Evidence first. Uncertainty visible.</span>
        </footer>
      </main>
      {source && (
        <div className="modal-backdrop" onClick={() => setSource(null)}>
          <section
            className="source-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Source evidence"
            onClick={(e) => e.stopPropagation()}
          >
            <header>
              <div>
                <FileText size={20} />
                <h2>{source.document_name}</h2>
              </div>
              <button
                className="icon-button"
                aria-label="Close source"
                onClick={() => setSource(null)}
              >
                <X size={21} />
              </button>
            </header>
            <div className="source-location">
              {source.page ? "Page " + source.page + " · " : ""}Lines{" "}
              {source.line_start}–{source.line_end}
            </div>
            <blockquote>{source.quote || source.text}</blockquote>
            <h3>Document passages</h3>
            <pre>{sourceText || "Loading authorized source…"}</pre>
          </section>
        </div>
      )}
    </div>
  );
}
