export type Fetcher = (input: string | URL | Request, init?: RequestInit) => Promise<Response>;

export async function readJson(response: Response, provider: string): Promise<unknown> {
  if (!response.ok) throw new Error(`${provider} request failed with HTTP ${response.status}`);
  const length = Number(response.headers.get("content-length") ?? 0);
  if (length > 3_000_000) throw new Error(`${provider} response exceeded the size limit`);
  return response.json();
}
