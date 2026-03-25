import type { DateRange } from "../types";

interface DateRangePickerProps {
	value: DateRange;
	onChange: (range: DateRange) => void;
	availableRange: [string, string];
}

export function DateRangePicker({
	value,
	onChange,
	availableRange,
}: DateRangePickerProps) {
	const today = new Date().toISOString().slice(0, 10);
	const minDate = availableRange[0];
	const maxDate = today < availableRange[1] ? today : availableRange[1];

	return (
		<div className="flex items-center gap-3">
			<label className="text-xs text-white/40 uppercase tracking-wide">
				From
			</label>
			<input
				type="date"
				value={value.start}
				min={minDate}
				max={value.end}
				onChange={(e) => onChange({ ...value, start: e.target.value })}
				className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-white/20 [color-scheme:dark]"
			/>
			<label className="text-xs text-white/40 uppercase tracking-wide">
				To
			</label>
			<input
				type="date"
				value={value.end}
				min={value.start}
				max={maxDate}
				onChange={(e) => onChange({ ...value, end: e.target.value })}
				className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-white/20 [color-scheme:dark]"
			/>
		</div>
	);
}
