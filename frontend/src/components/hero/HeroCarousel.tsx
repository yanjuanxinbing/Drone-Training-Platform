"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { HERO_SLIDES } from "@/lib/scenarios";
import styles from "./HeroCarousel.module.css";

const AUTO_INTERVAL = 7000;

export function HeroCarousel() {
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState<1 | -1>(1);
  const [progress, setProgress] = useState(0);
  const [videosReady, setVideosReady] = useState(false);
  const videoRefs = useRef<(HTMLVideoElement | null)[]>([]);
  const intervalRef = useRef<number | null>(null);

  useEffect(() => {
    // Preload all videos for snappy transitions
    videoRefs.current.forEach((v) => v?.load());
    setVideosReady(true);
  }, []);

  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setProgress(0);

    const stepAt = performance.now();
    const tick = () => {
      const elapsed = performance.now() - stepAt;
      const ratio = Math.min(1, elapsed / AUTO_INTERVAL);
      setProgress(ratio);
      if (ratio >= 1) {
        setDirection(1);
        setIndex((i) => (i + 1) % HERO_SLIDES.length);
      } else {
        intervalRef.current = requestAnimationFrame(tick);
      }
    };
    intervalRef.current = requestAnimationFrame(tick);
    return () => {
      if (intervalRef.current) cancelAnimationFrame(intervalRef.current);
    };
  }, [index]);

  const goTo = (i: number) => {
    if (i === index) return;
    setDirection(i > index ? 1 : -1);
    setIndex(((i % HERO_SLIDES.length) + HERO_SLIDES.length) % HERO_SLIDES.length);
  };

  const slide = HERO_SLIDES[index];

  return (
    <section className={styles.hero} aria-label="Featured indoor drone footage">
      {/* Index numerals — top-left */}
      <div className={styles.eyebrow}>
        <div className={styles.eyebrowInner}>
          <span className={styles.eyebrowText}>
            <span className={styles.eyebrowIndex}>00</span>
            <span>Hero Reel</span>
          </span>
          <span className={styles.eyebrowText}>
            <span>Wide-angle indoor flight</span>
          </span>
          <span className={styles.eyebrowText}>
            <span>4 clips · autoplay</span>
          </span>
        </div>
      </div>

      {/* Slide canvas — full-bleed video */}
      <div className={styles.canvas}>
        <AnimatePresence custom={direction} initial={false}>
          <motion.div
            key={slide.id}
            className={styles.slide}
            custom={direction}
            initial={{ x: direction * 60 + "vw", opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -direction * 60 + "vw", opacity: 0 }}
            transition={{ duration: 0.95, ease: [0.2, 0.8, 0.2, 1] }}
          >
            <KenBurnsVideo
              src={slide.video}
              poster={slide.poster}
              videoRef={(el) => (videoRefs.current[index] = el)}
              active
            />
            <div className={styles.overlay} />
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Caption overlay — Bauhaus typography */}
      <div className={styles.caption}>
        <motion.div
          key={slide.id + "-cap"}
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.2, 0.8, 0.2, 1], delay: 0.2 }}
          className={styles.captionInner}
        >
          <span className={styles.captionIndex}>
            {String(index + 1).padStart(2, "0")} / {String(HERO_SLIDES.length).padStart(2, "0")}
          </span>
          <h1 className={styles.captionTitle}>{slide.title}</h1>
          <p className={styles.captionCopy}>{slide.caption}</p>
          <p className={styles.captionMeta}>{slide.meta}</p>
        </motion.div>
      </div>

      {/* Slide counter — bottom-left */}
      <div className={styles.counter}>
        {HERO_SLIDES.map((s, i) => (
          <button
            key={s.id}
            type="button"
            aria-label={`Show slide ${i + 1}`}
            onClick={() => goTo(i)}
            className={`${styles.counterBtn} ${i === index ? styles.counterBtnActive : ""}`}
          >
            <span className={styles.counterNum}>{String(i + 1).padStart(2, "0")}</span>
            <span className={styles.counterLine} aria-hidden="true">
              <span
                className={styles.counterFill}
                style={{ transform: `scaleX(${i === index ? progress : i < index ? 1 : 0})` }}
              />
            </span>
          </button>
        ))}
      </div>

      {/* Scroll affordance */}
      <div className={styles.scroll}>
        <span>Scroll</span>
        <span className={styles.scrollLine} />
      </div>

      {/* Hidden preloaded videos */}
      <div style={{ position: "absolute", width: 0, height: 0, overflow: "hidden" }} aria-hidden="true">
        {HERO_SLIDES.map((s, i) => (
          <video
            key={s.id}
            ref={(el) => {
              videoRefs.current[i] = el;
            }}
            src={s.video}
            muted
            playsInline
            preload="metadata"
          />
        ))}
      </div>
    </section>
  );
}

/* ── Sub-component ───────────────────────────────────────────────────── */
function KenBurnsVideo({
  src,
  poster,
  active,
  videoRef,
}: {
  src: string;
  poster: string;
  active: boolean;
  videoRef: (el: HTMLVideoElement | null) => void;
}) {
  const [scale, setScale] = useState(1);
  const [errored, setErrored] = useState(false);

  useEffect(() => {
    if (!active) return;
    setScale(1.04);
    const t = setTimeout(() => setScale(1.18), 100);
    return () => clearTimeout(t);
  }, [active]);

  return (
    <motion.div
      className={styles.videoWrap}
      animate={{ scale }}
      transition={{ duration: 9, ease: [0.2, 0.8, 0.2, 1] }}
    >
      {!errored ? (
        <video
          ref={videoRef as React.RefCallback<HTMLVideoElement>}
          src={src}
          poster={poster}
          className={styles.video}
          autoPlay
          loop
          muted
          playsInline
          onError={() => setErrored(true)}
        />
      ) : (
        <div className={styles.fallback}>
          <div className={styles.fallbackGrid} aria-hidden="true" />
          <div className={styles.fallbackContent}>
            <span className={styles.fallbackLabel}>Sample placeholder</span>
            <span className={styles.fallbackName}>{src.split("/").pop()}</span>
            <span className={styles.fallbackHint}>
              Place your wide-angle indoor clips in <code>frontend/public/videos/</code>
            </span>
          </div>
        </div>
      )}
    </motion.div>
  );
}