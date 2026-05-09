"use client";

import { useEffect, useRef, useState } from "react";
import { apiUrl, fetchJson } from "@/lib/api";
import type { ActiveRollout } from "@/lib/types";

// Connects to /api/stream (SSE) and keeps the sessions list live.
// Falls back to a one-time GET /api/sessions on SSE error, then reconnects.
export function useSessions(): ActiveRollout[] {
  const [sessions, setSessions] = useState<ActiveRollout[]>([]);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Seed with HTTP snapshot so UI isn't blank on slow SSE connect
    fetchJson<ActiveRollout[]>("/api/sessions")
      .then(setSessions)
      .catch(() => {});

    function connect() {
      const es = new EventSource(apiUrl("/api/stream"));
      esRef.current = es;

      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data) as ActiveRollout[];
          setSessions(data);
        } catch {
          // malformed frame — ignore
        }
      };

      es.onerror = () => {
        // Browser auto-reconnects, but we also do a REST snapshot to cover the gap
        fetchJson<ActiveRollout[]>("/api/sessions")
          .then(setSessions)
          .catch(() => {});
      };
    }

    connect();
    return () => {
      esRef.current?.close();
    };
  }, []);

  return sessions;
}
