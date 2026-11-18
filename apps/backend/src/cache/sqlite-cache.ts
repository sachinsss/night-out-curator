import { createHash } from "node:crypto";
import { DatabaseSync } from "node:sqlite";
import { LRUCache } from "lru-cache";

export interface CacheKeyParts {
  agent: string;
  provider: string;
  model: string;
  promptVersion: string;
  schemaVersion: string;
  input: unknown;
}

interface HotEntry {
  value: unknown;
  expiresAt: number;
}

function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object")
    return `{${Object.entries(value as Record<string, unknown>)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, child]) => `${JSON.stringify(key)}:${canonical(child)}`)
      .join(",")}}`;
  return JSON.stringify(value);
}

export class SqliteCache {
  private readonly database: DatabaseSync;
  private readonly memory = new LRUCache<string, HotEntry>({ max: 500 });

  constructor(
    filename: string,
    private readonly now: () => number = Date.now,
  ) {
    this.database = new DatabaseSync(filename);
    this.database.exec(
      "PRAGMA journal_mode = WAL; CREATE TABLE IF NOT EXISTS cache_entries (cache_key TEXT PRIMARY KEY, value_json TEXT NOT NULL, expires_at INTEGER NOT NULL, created_at INTEGER NOT NULL)",
    );
  }

  createKey(parts: CacheKeyParts): string {
    return createHash("sha256").update(canonical(parts)).digest("hex");
  }

  get<T>(key: string): T | null {
    const hot = this.memory.get(key);
    if (hot && hot.expiresAt > this.now()) return hot.value as T;
    if (hot) this.memory.delete(key);
    const row = this.database
      .prepare("SELECT value_json, expires_at FROM cache_entries WHERE cache_key = ?")
      .get(key) as { value_json: string; expires_at: number } | undefined;
    if (!row) return null;
    if (row.expires_at <= this.now()) {
      this.database.prepare("DELETE FROM cache_entries WHERE cache_key = ?").run(key);
      return null;
    }
    const value = JSON.parse(row.value_json) as T;
    this.memory.set(key, { value, expiresAt: row.expires_at });
    return value;
  }

  set(key: string, value: unknown, ttlMs: number): void {
    const createdAt = this.now();
    const expiresAt = createdAt + ttlMs;
    this.database.exec("BEGIN IMMEDIATE");
    try {
      this.database
        .prepare(
          "INSERT INTO cache_entries(cache_key, value_json, expires_at, created_at) VALUES (?, ?, ?, ?) ON CONFLICT(cache_key) DO UPDATE SET value_json = excluded.value_json, expires_at = excluded.expires_at, created_at = excluded.created_at",
        )
        .run(key, JSON.stringify(value), expiresAt, createdAt);
      this.database.exec("COMMIT");
    } catch (error) {
      this.database.exec("ROLLBACK");
      throw error;
    }
    this.memory.set(key, { value, expiresAt });
  }

  deleteExpired(): number {
    for (const [key, entry] of this.memory.entries())
      if (entry.expiresAt <= this.now()) this.memory.delete(key);
    return Number(
      this.database.prepare("DELETE FROM cache_entries WHERE expires_at <= ?").run(this.now())
        .changes,
    );
  }

  close(): void {
    this.database.close();
  }
}
