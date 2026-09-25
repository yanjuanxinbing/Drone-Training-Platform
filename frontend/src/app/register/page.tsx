"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { setToken, setCachedUser } from "@/lib/auth";
import styles from "../login/page.module.css";
import regStyles from "./page.module.css";

export default function RegisterPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [agree, setAgree] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    if (password !== confirm) {
      setErr("两次密码不一致");
      return;
    }
    if (!agree) {
      setErr("请先阅读并同意用户协议");
      return;
    }
    setLoading(true);
    try {
      const res = await api.register(phone, password, confirm);
      setToken(res.access_token);
      setCachedUser(res.user);
      router.push("/account");
    } catch (e: any) {
      setErr(e?.message ?? "注册失败");
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
            <h2 className={styles.asideTitle}>Apply for a training record.</h2>
            <p className={styles.asideText}>
              Your phone number is your identifier — we don't ask for an email.
              Passwords are bcrypt-hashed. Existing Flet-era accounts
              auto-upgrade on first login.
            </p>
            <ul className={styles.list}>
              <li>Sessions persist for 7 days via JWT</li>
              <li>Progress is saved per scenario</li>
              <li>Address book for delivery orders</li>
              <li>Pilot certification in account settings</li>
            </ul>
          </aside>

          <form className={styles.form} onSubmit={onSubmit}>
            <header className={styles.formHead}>
              <span className={styles.formKicker}>Auth · 01</span>
              <h1 className={styles.formTitle}>Apply.</h1>
            </header>

            <label className={styles.field}>
              <span className={styles.label}>Phone</span>
              <input
                inputMode="numeric"
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
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={styles.input}
                required
                minLength={6}
              />
            </label>

            <label className={styles.field}>
              <span className={styles.label}>Confirm</span>
              <input
                type="password"
                placeholder="Re-enter your password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className={styles.input}
                required
                minLength={6}
              />
            </label>

            <label className={regStyles.agreeRow}>
              <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
              <span>I agree to the platform terms and privacy policy.</span>
            </label>

            {err && <p className={styles.error}>{err}</p>}

            <div className={styles.actions}>
              <Link href="/login" className={styles.link}>
                Already have an account? Sign in →
              </Link>
              <button type="submit" className={styles.submit} disabled={loading}>
                {loading ? "Applying…" : "Apply"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}