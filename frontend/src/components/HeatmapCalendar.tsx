import { useMemo } from "react";
import type { HeatmapDay } from "../types";

const CELL_SIZE = 13;
const CELL_GAP = 2;
const CELL_STEP = CELL_SIZE + CELL_GAP;
const DAYS_IN_WEEK = 7;
const LABEL_HEIGHT = 20;
const LEFT_PAD = 28;

const INTENSITY_COLORS = [
	"#161b22",
	"#0e4429",
	"#006d32",
	"#26a641",
	"#39d353",
] as const;

const DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""] as const;
const MONTH_NAMES = [
	"Jan",
	"Feb",
	"Mar",
	"Apr",
	"May",
	"Jun",
	"Jul",
	"Aug",
	"Sep",
	"Oct",
	"Nov",
	"Dec",
];

interface GridCell {
	date: string;
	count: number;
	intensity: 0 | 1 | 2 | 3 | 4;
	week: number;
	day: number;
}

function buildGrid(data: HeatmapDay[]): {
	cells: GridCell[];
	weeks: number;
	monthLabels: { label: string; week: number }[];
} {
	if (data.length === 0) return { cells: [], weeks: 0, monthLabels: [] };

	const dataMap = new Map(data.map((d) => [d.date, d]));

	// Find date range
	const dates = data.map((d) => d.date).sort();
	const startDate = new Date(dates[0] + "T00:00:00");
	const endDate = new Date(dates[dates.length - 1] + "T00:00:00");

	// Align start to the beginning of the week (Sunday)
	const alignedStart = new Date(startDate);
	alignedStart.setDate(alignedStart.getDate() - alignedStart.getDay());

	const cells: GridCell[] = [];
	const monthLabels: { label: string; week: number }[] = [];
	const currentDate = new Date(alignedStart);
	let week = 0;
	let lastMonth = -1;

	while (currentDate <= endDate) {
		const day = currentDate.getDay();
		const dateStr = currentDate.toISOString().slice(0, 10);
		const entry = dataMap.get(dateStr);

		// Track month labels
		const month = currentDate.getMonth();
		if (month !== lastMonth && day <= 3) {
			monthLabels.push({ label: MONTH_NAMES[month], week });
			lastMonth = month;
		}

		cells.push({
			date: dateStr,
			count: entry?.count ?? 0,
			intensity: entry?.intensity ?? 0,
			week,
			day,
		});

		currentDate.setDate(currentDate.getDate() + 1);
		if (currentDate.getDay() === 0) week++;
	}

	return { cells, weeks: week + 1, monthLabels };
}

interface HeatmapCalendarProps {
	data: HeatmapDay[];
}

export function HeatmapCalendar({ data }: HeatmapCalendarProps) {
	const { cells, weeks, monthLabels } = useMemo(() => buildGrid(data), [data]);

	if (cells.length === 0) {
		return (
			<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6">
				<h3 className="text-sm font-semibold text-white/60 mb-4 tracking-wide uppercase">
					Activity
				</h3>
				<p className="text-white/40 text-sm">No data in this range</p>
			</div>
		);
	}

	const svgWidth = LEFT_PAD + weeks * CELL_STEP + CELL_GAP;
	const svgHeight = LABEL_HEIGHT + DAYS_IN_WEEK * CELL_STEP + CELL_GAP;

	return (
		<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6">
			<h3 className="text-sm font-semibold text-white/60 mb-4 tracking-wide uppercase">
				Activity
			</h3>
			<div className="overflow-x-auto">
				<svg width={svgWidth} height={svgHeight} className="block">
					{/* Month labels */}
					{monthLabels.map(({ label, week }) => (
						<text
							key={`${label}-${week}`}
							x={LEFT_PAD + week * CELL_STEP}
							y={LABEL_HEIGHT - 4}
							className="fill-white/40"
							fontSize={10}
							fontFamily="system-ui"
						>
							{label}
						</text>
					))}
					{/* Day labels */}
					{DAY_LABELS.map(
						(label, i) =>
							label && (
								<text
									key={i}
									x={0}
									y={LABEL_HEIGHT + i * CELL_STEP + CELL_SIZE - 2}
									className="fill-white/40"
									fontSize={10}
									fontFamily="system-ui"
								>
									{label}
								</text>
							),
					)}
					{/* Cells */}
					{cells.map((cell) => (
						<rect
							key={cell.date}
							x={LEFT_PAD + cell.week * CELL_STEP}
							y={LABEL_HEIGHT + cell.day * CELL_STEP}
							width={CELL_SIZE}
							height={CELL_SIZE}
							rx={2}
							fill={INTENSITY_COLORS[cell.intensity]}
							className="transition-colors"
						>
							<title>
								{cell.date}: {cell.count.toLocaleString()} visits
							</title>
						</rect>
					))}
				</svg>
			</div>
			{/* Legend */}
			<div className="flex items-center gap-1 mt-3 text-xs text-white/40">
				<span>Less</span>
				{INTENSITY_COLORS.map((color, i) => (
					<div
						key={i}
						className="w-[10px] h-[10px] rounded-sm"
						style={{ backgroundColor: color }}
					/>
				))}
				<span>More</span>
			</div>
		</div>
	);
}
