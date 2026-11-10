import { generateText, Output, type LanguageModel } from "ai";
import { z } from "zod";

export interface StructuredRequest<T extends z.ZodType> {
  instructions: string;
  input: unknown;
  schema: T;
  abortSignal?: AbortSignal;
}
export interface StructuredResult<T> {
  output: T;
  usage: unknown;
  finishReason: string;
}
export interface LlmClient {
  generateStructured<T extends z.ZodType>(
    request: StructuredRequest<T>,
  ): Promise<StructuredResult<z.infer<T>>>;
}

export function extractJsonObject(text: string): unknown {
  const unfenced = text
    .trim()
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/\s*```$/i, "");
  const start = unfenced.indexOf("{");
  const end = unfenced.lastIndexOf("}");
  if (start < 0 || end <= start)
    throw new Error("The model response did not contain a JSON object.");
  return JSON.parse(unfenced.slice(start, end + 1));
}

export class AiSdkLlmClient implements LlmClient {
  constructor(private readonly model: LanguageModel) {}
  async generateStructured<T extends z.ZodType>(
    request: StructuredRequest<T>,
  ): Promise<StructuredResult<z.infer<T>>> {
    try {
      const result = await generateText({
        model: this.model,
        system: request.instructions,
        prompt: JSON.stringify(request.input),
        output: Output.object({ schema: request.schema }),
        ...(request.abortSignal ? { abortSignal: request.abortSignal } : {}),
      });
      return {
        output: request.schema.parse(result.output),
        usage: result.usage,
        finishReason: result.finishReason,
      };
    } catch (error) {
      if (!(error instanceof Error) || error.name !== "AI_NoObjectGeneratedError") throw error;
      const schema = z.toJSONSchema(request.schema, { unrepresentable: "any" });
      const repair = await generateText({
        model: this.model,
        system: `${request.instructions}\nThe previous structured response was invalid. Return exactly one JSON object and no prose or markdown. Every required field in this JSON Schema must be present:\n${JSON.stringify(schema)}`,
        prompt: JSON.stringify(request.input),
        ...(request.abortSignal ? { abortSignal: request.abortSignal } : {}),
      });
      try {
        return {
          output: request.schema.parse(extractJsonObject(repair.text)),
          usage: repair.usage,
          finishReason: repair.finishReason,
        };
      } catch {
        throw new Error("LLM returned invalid structured output after one repair attempt.");
      }
    }
  }
}
