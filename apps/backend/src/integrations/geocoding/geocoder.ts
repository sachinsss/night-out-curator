export interface ResolvedLocation {
  label: string;
  latitude: number;
  longitude: number;
}
export interface Geocoder {
  resolve(query: string): Promise<ResolvedLocation>;
}
