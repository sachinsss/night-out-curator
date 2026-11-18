import { DatabaseSync } from "node:sqlite";
import {
  RecommendationResponseSchema,
  type RecommendationRequest,
  type RecommendationResponse,
} from "@night-out/contracts";

export interface RecommendationRepository {
  save(request: RecommendationRequest, response: RecommendationResponse): void;
  find(requestId: string): RecommendationResponse | null;
}

export class MemoryRecommendationRepository implements RecommendationRepository {
  private readonly records = new Map<string, RecommendationResponse>();
  save(_request: RecommendationRequest, response: RecommendationResponse): void {
    this.records.set(response.requestId, response);
  }
  find(requestId: string): RecommendationResponse | null {
    return this.records.get(requestId) ?? null;
  }
}

export class SqliteRecommendationRepository implements RecommendationRepository {
  private readonly database: DatabaseSync;
  constructor(filename: string) {
    this.database = new DatabaseSync(filename);
    this.database.exec(
      "PRAGMA journal_mode = WAL; CREATE TABLE IF NOT EXISTS recommendations (request_id TEXT PRIMARY KEY, request_json TEXT NOT NULL, response_json TEXT NOT NULL, status TEXT NOT NULL, created_at INTEGER NOT NULL)",
    );
  }
  save(request: RecommendationRequest, response: RecommendationResponse): void {
    this.database
      .prepare(
        "INSERT OR REPLACE INTO recommendations(request_id, request_json, response_json, status, created_at) VALUES (?, ?, ?, ?, ?)",
      )
      .run(
        response.requestId,
        JSON.stringify(request),
        JSON.stringify(response),
        response.status,
        Date.now(),
      );
  }
  find(requestId: string): RecommendationResponse | null {
    const row = this.database
      .prepare("SELECT response_json FROM recommendations WHERE request_id = ?")
      .get(requestId) as { response_json: string } | undefined;
    return row ? RecommendationResponseSchema.parse(JSON.parse(row.response_json)) : null;
  }
  close(): void {
    this.database.close();
  }
}
