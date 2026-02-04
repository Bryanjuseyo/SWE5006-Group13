import { useEffect, useState } from "react";
import { getHealth } from "./api/client";

export default function App() {
  const [status, setStatus] = useState<string>("loading...");

  useEffect(() => {
    getHealth()
      .then((d) => setStatus(d.status))
      .catch(() => setStatus("error"));
  }, []);

  return (
    <div style={{ padding: 24, fontFamily: "system-ui, sans-serif" }}>
      <h1>CleanMatch</h1>
      <p>Backend health: {status}</p>
    </div>
  );
}
