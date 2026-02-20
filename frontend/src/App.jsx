import { useState } from "react";

export default function App() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sessionId = localStorage.getItem("chat_session_id");

  const runQuery = async () => {
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`http://localhost:5000/api/db/${sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, allow_write: false }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data?.error || "Something went wrong");
        return;
      }

      setResult(data);
    } catch (e) {
      setError("Failed to connect to server");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100vw",
        display: "flex",
        justifyContent: "center",
        alignItems: "flex-start",
        background: "#f6f7fb",
        paddingTop: 60,
        boxSizing: "border-box",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 900,
          background: "#ffffff",
          borderRadius: 12,
          boxShadow: "0 8px 24px rgba(0,0,0,0.08)",
          padding: 20,
          boxSizing: "border-box",
        }}
      >
        <h2 style={{ marginBottom: 12, textAlign: "center", color: "#111827" }}>
          🗄️ Database Console
        </h2>

        <textarea
          rows={3}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about your database (e.g. Show top 5 users)"
          style={{
            width: "100%",
            padding: 10,
            borderRadius: 8,
            border: "1px solid #d1d5db",
            outline: "none",
            fontSize: 14,
            boxSizing: "border-box",
            resize: "vertical",
            background: "#ffffff",
            color: "#111827",
          }}
        />

        <div style={{ display: "flex", justifyContent: "center", marginTop: 10 }}>
          <button
            onClick={runQuery}
            disabled={loading}
            style={{
              padding: "10px 18px",
              borderRadius: 8,
              border: "none",
              cursor: "pointer",
              background: loading ? "#9ca3af" : "#2563eb",
              color: "#ffffff",
              fontWeight: 600,
              fontSize: 14,
            }}
          >
            {loading ? "Running..." : "Run Query"}
          </button>
        </div>

        {error && (
          <div
            style={{
              marginTop: 12,
              padding: 10,
              borderRadius: 8,
              background: "#fee2e2",
              color: "#991b1b",
              fontSize: 14,
              textAlign: "center",
            }}
          >
            ❌ {error}
          </div>
        )}

        {result && (
          <div
            style={{
              marginTop: 16,
              border: "1px solid #e5e7eb",
              borderRadius: 10,
              overflow: "hidden",
              background: "#ffffff",
            }}
          >
            <div
              style={{
                padding: "8px 12px",
                background: "#f1f5f9",
                fontSize: 12,
                color: "#334155",
                borderBottom: "1px solid #e5e7eb",
              }}
            >
              <b>SQL:</b>{" "}
              <code style={{ wordBreak: "break-all", color: "#0f172a" }}>
                {result.sql}
              </code>
            </div>

            <div
              style={{
                maxHeight: 360,
                overflow: "auto",
                background: "#ffffff",
              }}
            >
              {result.columns && result.rows ? (
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    fontSize: 13,
                  }}
                >
                  <thead>
                    <tr>
                      {result.columns.map((col) => (
                        <th
                          key={col}
                          style={{
                            textAlign: "left",
                            padding: "8px 10px",
                            background: "#f3f4f6",
                            borderBottom: "1px solid #e5e7eb",
                            position: "sticky",
                            top: 0,
                          }}
                        >
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.rows.map((row, i) => (
                      <tr key={i}>
                        {row.map((cell, j) => (
                          <td
                            key={j}
                            style={{
                              padding: "8px 10px",
                              borderBottom: "1px solid #f1f5f9",
                              maxWidth: 260,
                              wordBreak: "break-word",
                              whiteSpace: "pre-wrap",
                              color: "#111827",
                            }}
                          >
                            {cell === null ? "NULL" : String(cell)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <pre style={{ padding: 12, margin: 0 }}>
                  {JSON.stringify(result, null, 2)}
                </pre>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}