export interface TransitRealtimeStatus {
  status: "on_time" | "delayed" | "alert" | "unavailable";
  delayMinutes: number | null;
  alerts: string[];
  checkedAt: string;
}
export interface TransitRealtimeClient {
  getStatus(routeIds: string[]): Promise<TransitRealtimeStatus>;
}
