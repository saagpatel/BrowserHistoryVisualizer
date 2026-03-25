import {
	Area,
	AreaChart,
	ReferenceLine,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import type { ProductivityPoint } from "../types";

interface ProductivityCurveProps {
	data: ProductivityPoint[];
}

function formatHour(hour: number): string {
	if (hour === 0) return "12am";
	if (hour === 12) return "12pm";
	return hour < 12 ? `${hour}am` : `${hour - 12}pm`;
}

export function ProductivityCurve({ data }: ProductivityCurveProps) {
	if (data.length === 0) {
		return (
			<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6 h-full">
				<h3 className="text-sm font-semibold text-white/60 mb-4 tracking-wide uppercase">
					Productivity
				</h3>
				<p className="text-white/40 text-sm">No data in this range</p>
			</div>
		);
	}

	const chartData = data.map((d) => ({
		hour: d.hour,
		label: formatHour(d.hour),
		focus: d.focus_minutes,
		distraction: d.distraction_minutes,
		ratio: d.ratio,
	}));

	return (
		<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6 h-full">
			<h3 className="text-sm font-semibold text-white/60 mb-4 tracking-wide uppercase">
				Productivity
			</h3>
			<ResponsiveContainer width="100%" height={240}>
				<AreaChart
					data={chartData}
					margin={{ top: 4, right: 8, bottom: 0, left: 0 }}
				>
					<defs>
						<linearGradient id="focusGrad" x1="0" y1="0" x2="0" y2="1">
							<stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
							<stop offset="95%" stopColor="#06b6d4" stopOpacity={0.02} />
						</linearGradient>
						<linearGradient id="distractGrad" x1="0" y1="0" x2="0" y2="1">
							<stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
							<stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
						</linearGradient>
					</defs>
					<XAxis
						dataKey="label"
						tick={{ fill: "#6b7280", fontSize: 10 }}
						tickLine={false}
						axisLine={false}
						interval={5}
					/>
					<YAxis
						tick={{ fill: "#6b7280", fontSize: 10 }}
						tickLine={false}
						axisLine={false}
						width={40}
						tickFormatter={(v: number) => `${v}m`}
					/>
					<ReferenceLine
						x={formatHour(12)}
						stroke="rgba(255,255,255,0.1)"
						strokeDasharray="3 3"
					/>
					<Tooltip
						content={({ payload, label }) => {
							if (!payload || payload.length === 0) return null;
							const focus = payload.find((p) => p.dataKey === "focus");
							const distraction = payload.find(
								(p) => p.dataKey === "distraction",
							);
							return (
								<div
									style={{
										backgroundColor: "#161b22",
										border: "1px solid rgba(255,255,255,0.1)",
										borderRadius: 8,
										padding: "8px 12px",
									}}
								>
									<p style={{ color: "#fff", fontWeight: 600, fontSize: 13 }}>
										{label}
									</p>
									{focus && (
										<p style={{ color: "#06b6d4", fontSize: 12, marginTop: 2 }}>
											Focus: {Number(focus.value)} min
										</p>
									)}
									{distraction && (
										<p style={{ color: "#ef4444", fontSize: 12, marginTop: 2 }}>
											Distraction: {Number(distraction.value)} min
										</p>
									)}
								</div>
							);
						}}
					/>
					<Area
						type="monotone"
						dataKey="focus"
						stackId="1"
						stroke="#06b6d4"
						fill="url(#focusGrad)"
						strokeWidth={2}
					/>
					<Area
						type="monotone"
						dataKey="distraction"
						stackId="1"
						stroke="#ef4444"
						fill="url(#distractGrad)"
						strokeWidth={2}
					/>
				</AreaChart>
			</ResponsiveContainer>
			{/* Legend */}
			<div className="flex items-center gap-4 mt-2 text-xs text-white/40">
				<span className="flex items-center gap-1.5">
					<span className="w-2.5 h-2.5 rounded-full bg-cyan-500" />
					Focus
				</span>
				<span className="flex items-center gap-1.5">
					<span className="w-2.5 h-2.5 rounded-full bg-red-500" />
					Distraction
				</span>
			</div>
		</div>
	);
}
