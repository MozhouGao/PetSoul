/**
 * Authenticated API wrapper for PetSoul backend.
 * Uses Auth0 getAccessTokenSilently via setTokenGetter().
 */

type TokenGetter = () => Promise<string>;

let _getToken: TokenGetter | null = null;

export function setTokenGetter(fn: TokenGetter) {
  _getToken = fn;
}

async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  if (_getToken) {
    const token = await _getToken();
    headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(url, { ...options, headers });
}

// ─── Auth ───────────────────────────────────────────

export async function syncUser(): Promise<{ synced: boolean; user_id: string }> {
  const res = await authFetch("/auth/sync", { method: "POST" });
  if (!res.ok) throw new Error(`Sync failed: ${res.status}`);
  return res.json();
}

export async function getMe(): Promise<{ id: string; email: string; name: string }> {
  const res = await authFetch("/auth/me");
  if (!res.ok) throw new Error(`Get me failed: ${res.status}`);
  return res.json();
}

// ─── Pets ───────────────────────────────────────────

export interface PetResponse {
  id: number;
  name: string;
  species: string;
  breed: string;
  breed_confidence: number;
  profile: Record<string, unknown>;
  texture_prompt: string;
  model_url: string | null;
  created_at: string;
}

export async function listPets(): Promise<PetResponse[]> {
  const res = await authFetch("/pets/");
  if (!res.ok) throw new Error(`List pets failed: ${res.status}`);
  return res.json();
}

export async function createPet(file: File, name: string): Promise<PetResponse> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("name", name);
  const res = await authFetch("/pets/", { method: "POST", body: fd });
  if (!res.ok) throw new Error(`Create pet failed: ${res.status}`);
  return res.json();
}

export async function deletePet(id: number): Promise<void> {
  const res = await authFetch(`/pets/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Delete pet failed: ${res.status}`);
}

// ─── Motion ─────────────────────────────────────────

export interface MotionResult {
  success: boolean;
  frames_analyzed: number;
  motion_stats: Record<string, number>;
  personality: Record<string, number>;
}

export async function analyzeVideo(file: File, petId?: number): Promise<MotionResult> {
  const fd = new FormData();
  fd.append("file", file);
  if (petId !== undefined) fd.append("pet_id", String(petId));
  const res = await authFetch("/motion/analyze-video", { method: "POST", body: fd });
  if (!res.ok) throw new Error(`Analyze video failed: ${res.status}`);
  return res.json();
}

export interface AudioResult {
  success: boolean;
  audio_stats: Record<string, number>;
  classification: {
    vocal_type: string;
    vocal_confidence: number;
    emotion: string;
    emotion_confidence: number;
  };
}

export async function analyzeAudio(file: File, petId?: number): Promise<AudioResult> {
  const fd = new FormData();
  fd.append("file", file);
  if (petId !== undefined) fd.append("pet_id", String(petId));
  const res = await authFetch("/motion/analyze-audio", { method: "POST", body: fd });
  if (!res.ok) throw new Error(`Analyze audio failed: ${res.status}`);
  return res.json();
}

export async function getPersonality(petId: number): Promise<Record<string, number>> {
  const res = await authFetch(`/motion/personality/${petId}`);
  if (!res.ok) throw new Error(`Get personality failed: ${res.status}`);
  return res.json();
}

// ─── Export ─────────────────────────────────────────

export async function exportUnity(petId: number): Promise<Blob> {
  const res = await authFetch(`/export/${petId}/unity`, { method: "POST" });
  if (!res.ok) throw new Error(`Export failed: ${res.status}`);
  return res.blob();
}
