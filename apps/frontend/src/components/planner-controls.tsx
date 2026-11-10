import { useState } from "react";
import { CalendarDays, ChevronDown } from "lucide-react";
import { format } from "date-fns";
import { Button } from "./ui/button";
import { Calendar } from "./ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";

type Option = { value: string; label: string };
export function PlannerSelect({
  name,
  label,
  options,
  defaultValue = "",
  value,
  onValueChange,
  compact = false,
}: {
  name?: string;
  label: string;
  options: Option[];
  defaultValue?: string;
  value?: string;
  onValueChange?(value: string): void;
  compact?: boolean;
}) {
  const [local, setLocal] = useState(defaultValue);
  const selected = value ?? local;
  const hasEmpty = options.some((option) => option.value === "");
  return (
    <>
      {name && <input type="hidden" name={name} value={selected} />}
      <Select
        value={selected || (hasEmpty ? "__none" : "")}
        onValueChange={(next) => {
          const decoded = next === "__none" ? "" : next;
          setLocal(decoded);
          onValueChange?.(decoded);
        }}
      >
        <SelectTrigger
          id={`planner-${label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
          aria-label={label}
          className={compact ? "planner-control cuisine-add" : "planner-control"}
        >
          <SelectValue
            placeholder={compact ? <ChevronDown aria-hidden="true" /> : "Choose an option"}
          />
        </SelectTrigger>
        <SelectContent position="popper" sideOffset={6} className="planner-select-menu">
          <SelectGroup>
            {options.map((option) => (
              <SelectItem key={option.value || "__none"} value={option.value || "__none"}>
                {option.label}
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>
    </>
  );
}

export function PlannerDatePicker() {
  const [date, setDate] = useState<Date>();
  const [open, setOpen] = useState(false);
  return (
    <>
      <input type="hidden" name="date" value={date ? format(date, "yyyy-MM-dd") : ""} />
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            className={`planner-control date-trigger ${date ? "" : "is-placeholder"}`}
            id="planner-date"
            aria-label="Date"
          >
            <span>{date ? format(date, "EEE, MMM d") : "Choose a date"}</span>
            <CalendarDays aria-hidden="true" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="calendar-popover" align="start" sideOffset={8}>
          <Calendar
            mode="single"
            selected={date}
            onSelect={(next) => {
              setDate(next);
              setOpen(false);
            }}
            autoFocus
          />
          <div className="calendar-footer">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                setDate(undefined);
                setOpen(false);
              }}
            >
              Clear
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setDate(new Date());
                setOpen(false);
              }}
            >
              Today
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </>
  );
}
