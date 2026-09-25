"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { setToken, setCachedUser } from "@/lib/auth";
import styles from "./page.module.css";

export default function LoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setLoading(true);
    try {
      const res = await api.login(phone, password);
      setToken(res.access_token);
      setCachedUser(res.user);
      router.push("/account");
    } catch (e: any) {
      setErr(e?.message ?? "登录失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.grid}>
          <aside className={styles.aside}>
            <span className={styles.num}>00</span>
            <h2 className={styles.asideTitle}>Sign in to your training record.</h2>
            <p className={styles.asideText}>
              Access your scenario progress, address book, and order history.
              Authentication is JWT-based; sessions persist for seven days.
            </p>
            <ul className={styles.list}>
              <li>Six canonical training environments</li>
              <li>Real-time AirSim fallback bridge</li>
              <li>Scenario progress and telemetry</li>
              <li>Address book for delivery orders</li>
            </ul>
          </aside>

          <form className={styles.form} onSubmit={onSubmit}>
            <header className={styles.formHead}>
              <span className={styles.formKicker}>Auth · 00</span>
              <h1 className={styles.formTitle}>Sign in.</h1>
            </header>

            <label className={styles.field}>
              <span className={styles.label}>Phone</span>
              <input
                inputMode="numeric"
                autoComplete="tel"
                placeholder="11-digit phone number"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className={styles.input}
                required
              />
            </label>

            <label className={styles.field}>
              <span className={styles.label}>Password</span>
              <input
                type="password"
                autoComplete="current-password"
                placeholder="Your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={styles.input}
                required
              />
            </label>

            {err && <p className={styles.error}>{err}</p>}

            <div className={styles.actions}>
              <Link href="/register" className={styles.link}>
                Need an account? Apply →
              </Link>
              <button type="submit" className={styles.submit} disabled={loading}>
                {loading ? "Signing in…" : "Sign in"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}