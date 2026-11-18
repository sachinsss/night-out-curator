import type { Fetcher } from "../http.js";
import { readJson } from "../http.js";
import type { WeatherClient, WeatherContext, WeatherInput } from "./weather-client.js";

export class GoogleWeatherClient implements WeatherClient {
  constructor(
    private readonly apiKey: string,
    private readonly fetcher: Fetcher = fetch,
  ) {}

  async getHourly(input: WeatherInput): Promise<WeatherContext> {
    const url = new URL("https://weather.googleapis.com/v1/forecast/hours:lookup");
    url.searchParams.set("key", this.apiKey);
    url.searchParams.set("location.latitude", String(input.latitude));
    url.searchParams.set("location.longitude", String(input.longitude));
    url.searchParams.set("hours", String(Math.min(24, Math.max(1, input.hours))));
    url.searchParams.set("unitsSystem", "IMPERIAL");
    const response = await this.fetcher(url, { signal: AbortSignal.timeout(10_000) });
    const data = (await readJson(response, "Google Weather")) as {
      forecastHours?: Array<Record<string, any>>;
    };
    const hours = data.forecastHours ?? [];
    const rain = hours.some(
      (hour) =>
        Number(hour.precipitation?.probability?.percent ?? 0) >= 50 ||
        /rain|storm/i.test(hour.weatherCondition?.description?.text ?? ""),
    );
    const descriptions = [
      ...new Set(hours.map((hour) => hour.weatherCondition?.description?.text).filter(Boolean)),
    ];
    return {
      summary: descriptions.join(", ") || "Weather forecast unavailable.",
      warnings: rain ? ["Rain is likely; prefer indoor venues."] : [],
      retrievedAt: new Date().toISOString(),
    };
  }
}
