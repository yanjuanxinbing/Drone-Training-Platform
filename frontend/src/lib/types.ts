// TypeScript types mirroring backend Pydantic schemas.

export type UserPublic = {
  phone: string;
  nick_name: string;
  gender: string;
  birthday: string;
  addresses: unknown[]; // legacy field, retained for forward-compat
  is_real_name_verified: boolean;
  is_pilot_verified: boolean;
};

export type Scenario = {
  id: string;
  slug: string;
  name: string;
  name_zh: string;
  tagline: string;
  tagline_zh: string;
  difficulty: string;
  duration_minutes: number;
  objectives: string[];
  objectives_zh: string[];
  color: string;
  accent: string;
  icon: string;
  metrics: Record<string, number | string>;
};

export type ScenarioList = { items: Scenario[] };

export type ProgressEntry = {
  scenario_slug: string;
  attempts: number;
  best_score: number;
  best_duration_seconds: number;
  completed: boolean;
  last_played: string | null;
};