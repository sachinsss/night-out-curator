export interface WeatherInput {
  latitude: number;
  longitude: number;
  hours: number;
}
export interface WeatherContext {
  summary: string;
  warnings: string[];
  retrievedAt: string;
}
export interface WeatherClient {
  getHourly(input: WeatherInput): Promise<WeatherContext>;
}
