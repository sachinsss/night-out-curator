import { useState, type FormEvent } from "react";
import type { MapPoint } from "./map-point";
import {
  ArrowRight,
  CalendarDays,
  CarFront,
  Clock3,
  Footprints,
  Layers,
  Leaf,
  LocateFixed,
  Map,
  MapPin,
  Pencil,
  Ban,
  Sparkles,
  TrainFront,
  UsersRound,
  Utensils,
  Bike,
} from "lucide-react";
import type { ResolvedLocation } from "./api";
import { BrandMark } from "./BrandMark";
import { Field, FieldLabel, FieldGroup } from "./components/ui/field";
import { PlannerDatePicker, PlannerSelect } from "./components/planner-controls";
import { MapPicker } from "./MapPicker";

export type Transportation = "walking" | "driving" | "rideshare" | "transit";
interface Props {
  onReturnToResults?: (() => void) | undefined;
  loading: boolean;
  error: string;
  location: ResolvedLocation | null;
  mapPoint: MapPoint;
  showMap: boolean;
  transportation: Transportation;
  onSubmit(event: FormEvent<HTMLFormElement>): void;
  onUseLocation(): void;
  onToggleMap(): void;
  onMapChange(point: MapPoint): void;
  onLocationQuery(): void;
  onTransportation(value: Transportation): void;
}

export function PlannerForm(props: Props) {
  const [stops, setStops] = useState(3);
  const [mood, setMood] = useState("Lively");
  const [prompt, setPrompt] = useState("");
  const [preferences, setPreferences] = useState("");
  function applyPrompt() {
    if (prompt.trim()) {
      setPreferences(prompt.trim());
      document.getElementById("night-preferences")?.focus();
    }
  }
  const [cuisines, setCuisines] = useState(["Italian", "Mexican", "American"]);
  const travel = [
    { value: "walking", label: "Walking", icon: Footprints },
    { value: "driving", label: "Driving", icon: CarFront },
    { value: "rideshare", label: "Rideshare", icon: Bike },
    { value: "transit", label: "Public transit", icon: TrainFront },
  ] as const;
  return (
    <form className="planner-form reference-planner" onSubmit={props.onSubmit} noValidate>
      <header className="planner-title">
        <div>
          <h2>Plan your night</h2>
        </div>
        {props.onReturnToResults && (
          <button
            type="button"
            className="return-to-results"
            disabled={props.loading}
            onClick={props.onReturnToResults}
          >
            Back to results
            <ArrowRight size={15} aria-hidden="true" />
          </button>
        )}
      </header>
      <div className="prompt-bar">
        <BrandMark surface="light" size={30} />
        <input
          aria-label="Describe your ideal night"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              applyPrompt();
            }
          }}
          placeholder="Add a note for your itinerary"
        />
        <button
          type="button"
          aria-label="Use description as additional preferences"
          onClick={applyPrompt}
          disabled={!prompt.trim()}
        >
          <ArrowRight />
        </button>
      </div>

      <FieldGroup className="reference-top-grid">
        <div className="location-field">
          <Field className="field">
            <FieldLabel htmlFor="planner-location">
              <MapPin />
              Location
            </FieldLabel>
            <input
              id="planner-location"
              aria-label="Address, neighborhood, or landmark"
              name="locationQuery"
              defaultValue="Phoenix, AZ"
              placeholder="City or neighborhood"
              onChange={props.onLocationQuery}
              aria-describedby="location-help"
            />
          </Field>
          <div className="location-tools">
            <button
              type="button"
              title="Use my location"
              aria-label="Use my location"
              onClick={props.onUseLocation}
            >
              <LocateFixed size={14} />
            </button>
            <button
              type="button"
              title="Choose on map"
              aria-label="Choose on map"
              onClick={props.onToggleMap}
            >
              <Map size={14} />
            </button>
          </div>
        </div>
        <Field className="field">
          <FieldLabel htmlFor="planner-date">
            <CalendarDays />
            Date
          </FieldLabel>
          <PlannerDatePicker />
        </Field>
        <Field className="field">
          <FieldLabel htmlFor="planner-start-time">
            <Clock3 />
            Start time
          </FieldLabel>
          <PlannerSelect
            name="startTime"
            label="Start time"
            defaultValue="19:30"
            options={Array.from({ length: 48 }, (_, i) => {
              const hour = Math.floor(i / 2);
              const minute = i % 2 ? "30" : "00";
              return {
                value: `${String(hour).padStart(2, "0")}:${minute}`,
                label: `${hour % 12 || 12}:${minute} ${hour < 12 ? "AM" : "PM"}`,
              };
            })}
          />
        </Field>
        <Field className="field">
          <FieldLabel htmlFor="planner-party-size">
            <UsersRound />
            Party size
          </FieldLabel>
          <PlannerSelect
            name="partySize"
            label="Party size"
            defaultValue="4"
            options={Array.from({ length: 20 }, (_, i) => ({
              value: String(i + 1),
              label: `${i + 1} ${i === 0 ? "person" : "people"}`,
            }))}
          />
        </Field>
      </FieldGroup>
      <p id="location-help" className="reference-location-help">
        {props.location ? `Using ${props.location.label}` : ""}
      </p>
      {props.showMap && (
        <MapPicker
          value={props.mapPoint}
          onChange={props.onMapChange}
          onClose={props.onToggleMap}
        />
      )}
      <FieldGroup className="reference-middle-grid">
        <Field className="field">
          <FieldLabel htmlFor="planner-budget-person">
            <Layers />
            Budget / person
          </FieldLabel>
          <PlannerSelect
            name="budget"
            label="Budget / person"
            defaultValue="125"
            options={[
              { value: "50", label: "$25 - $50" },
              { value: "75", label: "$50 - $75" },
              { value: "125", label: "$75 - $125" },
              { value: "200", label: "$125 - $200" },
              { value: "300", label: "$200 - $300" },
            ]}
          />
        </Field>
        <div className="field">
          <span>
            <CarFront />
            Number of stops
          </span>
          <input type="hidden" name="stopCount" value={stops} />
          <div className="choice-row stops">
            {[1, 2, 3, 4].map((n) => (
              <button
                type="button"
                key={n}
                aria-pressed={stops === n}
                className={stops === n ? "selected-solid" : ""}
                onClick={() => setStops(n)}
              >
                {n}
              </button>
            ))}
          </div>
        </div>
        <div className="field">
          <span>
            <Layers />
            Mood
          </span>
          <input type="hidden" name="mood" value={mood} />
          <div className="choice-row">
            {["Chill", "Lively", "Romantic"].map((m) => (
              <button
                type="button"
                key={m}
                aria-pressed={mood === m}
                className={mood === m ? "selected-outline" : ""}
                onClick={() => setMood(m)}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </FieldGroup>
      <div className="field transport-field">
        <span>
          <CarFront />
          Transportation
        </span>
        <div className="choice-row transport-options">
          {travel.map(({ value, label, icon: Icon }) => (
            <button
              type="button"
              key={value}
              aria-pressed={props.transportation === value}
              className={props.transportation === value ? "selected-outline" : ""}
              onClick={() => props.onTransportation(value)}
            >
              <Icon size={20} />
              {label}
            </button>
          ))}
        </div>
      </div>
      {props.transportation === "transit" && (
        <Field className="field transit-priority">
          <FieldLabel htmlFor="planner-transit-priority">Transit priority</FieldLabel>
          <PlannerSelect
            name="transitPreference"
            label="Transit priority"
            defaultValue="less_walking"
            options={[
              { value: "less_walking", label: "Less walking" },
              { value: "fewer_transfers", label: "Fewer transfers" },
            ]}
          />
        </Field>
      )}
      <FieldGroup className="reference-bottom-grid">
        <div className="field cuisine-field">
          <span>
            <Utensils />
            Cuisine preferences
          </span>
          <input type="hidden" name="cuisine" value={cuisines.join(",")} />
          <div className="cuisine-control">
            {cuisines.map((c) => (
              <button
                type="button"
                key={c}
                aria-label={`Remove ${c} cuisine`}
                onClick={() => setCuisines(cuisines.filter((v) => v !== c))}
              >
                {c}
                <span aria-hidden="true">�</span>
              </button>
            ))}
            <PlannerSelect
              label="Add cuisine"
              value=""
              compact
              options={["Italian", "Mexican", "American", "Indian", "Japanese", "Thai"]
                .filter((c) => !cuisines.includes(c))
                .map((c) => ({ value: c, label: c }))}
              onValueChange={(c) => setCuisines([...cuisines, c])}
            />
          </div>
        </div>
        <Field className="field">
          <FieldLabel htmlFor="planner-dietary-requirements">
            <Leaf />
            Dietary requirements
          </FieldLabel>
          <PlannerSelect
            name="dietary"
            label="Dietary requirements"
            options={[
              { value: "", label: "No restrictions" },
              ...["Vegetarian", "Vegan", "Gluten-free"].map((d) => ({ value: d, label: d })),
            ]}
          />
        </Field>
        <Field className="field">
          <FieldLabel htmlFor="planner-categories-to-exclude">
            <Ban />
            Categories to exclude
          </FieldLabel>
          <PlannerSelect
            name="excluded"
            label="Categories to exclude"
            options={[
              { value: "", label: "None" },
              { value: "Bars, Clubs", label: "Bars, Clubs" },
              { value: "Clubs", label: "Clubs" },
              { value: "Fast food", label: "Fast food" },
            ]}
          />
        </Field>
      </FieldGroup>
      <label className="additional-preferences">
        <span>
          <Pencil />
          Additional preferences
        </span>
        <input
          id="night-preferences"
          name="preferences"
          value={preferences}
          onChange={(e) => setPreferences(e.target.value)}
          placeholder="e.g., rooftop seating, live music, quiet spots..."
        />
      </label>
      <footer className="planner-footer">
        <div className="form-feedback" aria-live="polite">
          {props.error && (
            <p role="alert" className="form-error">
              {props.error}
            </p>
          )}
        </div>
        <button
          className="button button-primary"
          disabled={props.loading}
          aria-busy={props.loading}
        >
          {props.loading ? (
            <>
              <span className="spinner" />
              Curating your night
            </>
          ) : (
            <>
              <Sparkles />
              Generate Itinerary
              <ArrowRight />
            </>
          )}
        </button>
      </footer>
    </form>
  );
}
