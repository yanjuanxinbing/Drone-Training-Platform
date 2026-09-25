"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getToken, clearToken } from "@/lib/auth";
import type { UserPublic } from "@/lib/types";
import styles from "./page.module.css";

export default function AccountPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserPublic | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => {
        clearToken();
        router.push("/login");
      })
      .finally(() => setLoading(false));
  }, [router]);

  if (loading) return <div className={styles.loading}>Loading profile…</div>;
  if (!user) return null;

  return (
    <div className={styles.page}>
      <div className={styles.container}>
        <div className={styles.eyebrowRow}>
          <span>00</span>
          <span>Account</span>
          <span>{user.phone}</span>
          <span>{user.nick_name}</span>
        </div>

        <div className={styles.heroBlock}>
          <RevealRow>
            <h1 className={styles.heroName}>{user.nick_name}</h1>
            <p className={styles.heroMeta}>
              <span>{user.phone}</span>
              <span>{user.gender}</span>
              <span>{user.birthday || "Birthday — not set"}</span>
            </p>
          </RevealRow>
          <RevealRow delay={0.05}>
            <div className={styles.heroChips}>
              <span className={user.is_real_name_verified ? styles.chipOn : styles.chipOff}>
                Real-name · {user.is_real_name_verified ? "verified" : "pending"}
              </span>
              <span className={user.is_pilot_verified ? styles.chipOn : styles.chipOff}>
                Pilot · {user.is_pilot_verified ? "verified" : "pending"}
              </span>
            </div>
          </RevealRow>
        </div>

        <div className={styles.cards}>
          <Link href="/training" className={styles.card}>
            <span className={styles.cardNum}>00</span>
            <h2 className={styles.cardTitle}>Training</h2>
            <p className={styles.cardCopy}>Continue your scenario track.</p>
            <span className={styles.cardArrow}>→</span>
          </Link>
          <Link href="/account/progress" className={styles.card}>
            <span className={styles.cardNum}>01</span>
            <h2 className={styles.cardTitle}>Progress</h2>
            <p className={styles.cardCopy}>Per-scenario scores, attempts, durations.</p>
            <span className={styles.cardArrow}>→</span>
          </Link>
        </div>

        <button
          className={styles.signOut}
          onClick={() => {
            clearToken();
            router.push("/");
          }}
        >
          Sign out
        </button>
      </div>
    </div>
  );
}

function RevealRow({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  return (
    <div
      style={{
        animation: `revealUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) ${delay}s both`,
      }}
    >
      {children}
      <style jsx>{`
        @keyframes revealUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}