import GtfsRealtimeBindings from "gtfs-realtime-bindings";
import type { Fetcher } from "../http.js";
import type { TransitRealtimeClient, TransitRealtimeStatus } from "./transit-realtime-client.js";

interface Cached {
  expiresAt: number;
  messages: Array<InstanceType<typeof GtfsRealtimeBindings.transit_realtime.FeedMessage>>;
}

export class ValleyMetroRealtimeClient implements TransitRealtimeClient {
  private cache: Cached | null = null;
  constructor(
    private readonly urls: string[],
    private readonly fetcher: Fetcher = fetch,
    private readonly ttlMs = 30_000,
  ) {}

  async getStatus(routeIds: string[]): Promise<TransitRealtimeStatus> {
    const checkedAt = new Date().toISOString();
    if (!this.urls.length)
      return {
        status: "unavailable",
        delayMinutes: null,
        alerts: ["Valley Metro real-time feeds are not configured."],
        checkedAt,
      };
    try {
      const messages = await this.getMessages();
      const wanted = new Set(routeIds.map((id) => id.trim().toLowerCase()).filter(Boolean));
      let delaySeconds = 0;
      const alerts = new Set<string>();
      for (const message of messages)
        for (const entity of message.entity) {
          const tripRoute = entity.tripUpdate?.trip?.routeId?.trim().toLowerCase();
          if (tripRoute && wanted.has(tripRoute))
            for (const update of entity.tripUpdate?.stopTimeUpdate ?? []) {
              delaySeconds = Math.max(
                delaySeconds,
                Number(update.arrival?.delay ?? 0),
                Number(update.departure?.delay ?? 0),
              );
            }
          if (entity.alert) {
            const affected = entity.alert.informedEntity ?? [];
            const applies =
              affected.length === 0 ||
              affected.some(
                (item) => !item.routeId || wanted.has(item.routeId.trim().toLowerCase()),
              );
            if (applies) {
              const text = entity.alert.headerText?.translation?.find((item) => item.text)?.text;
              if (text) alerts.add(text);
            }
          }
        }
      const delayMinutes = delaySeconds > 0 ? Math.ceil(delaySeconds / 60) : null;
      return {
        status: alerts.size ? "alert" : delayMinutes ? "delayed" : "on_time",
        delayMinutes,
        alerts: [...alerts],
        checkedAt,
      };
    } catch {
      return {
        status: "unavailable",
        delayMinutes: null,
        alerts: ["Valley Metro real-time information is temporarily unavailable."],
        checkedAt,
      };
    }
  }

  private async getMessages() {
    if (this.cache && this.cache.expiresAt > Date.now()) return this.cache.messages;
    const messages = await Promise.all(
      this.urls.map(async (url) => {
        const response = await this.fetcher(url, { signal: AbortSignal.timeout(8_000) });
        if (!response.ok) throw new Error(`Valley Metro returned HTTP ${response.status}`);
        const bytes = new Uint8Array(await response.arrayBuffer());
        if (bytes.byteLength > 5_000_000)
          throw new Error("Valley Metro feed exceeded the size limit");
        return GtfsRealtimeBindings.transit_realtime.FeedMessage.decode(bytes);
      }),
    );
    this.cache = { messages, expiresAt: Date.now() + this.ttlMs };
    return messages;
  }
}
