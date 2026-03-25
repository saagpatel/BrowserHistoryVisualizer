import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { CATEGORY_COLORS, type Category, type TopicSlice } from "../types";

interface TopicDonutProps {
	data: TopicSlice[];
}

export function TopicDonut({ data }: TopicDonutProps) {
	if (data.length === 0) {
		return (
			<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6 h-full">
				<h3 className="text-sm font-semibold text-white/60 mb-4 tracking-wide uppercase">
					Topics
				</h3>
				<p className="text-white/40 text-sm">No data in this range</p>
			</div>
		);
	}

	const totalVisits = data.reduce((sum, d) => sum + d.visits, 0);

	const chartData = data.map((d) => ({
		name: d.category,
		value: d.visits,
		minutes: d.estimated_minutes,
		percentage: d.percentage,
		fill:
			CATEGORY_COLORS[d.category as Category] ?? CATEGORY_COLORS.uncategorized,
	}));

	return (
		<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6 h-full">
			<h3 className="text-sm font-semibold text-white/60 mb-4 tracking-wide uppercase">
				Topics
			</h3>
			<div className="relative">
				<ResponsiveContainer width="100%" height={280}>
					<PieChart>
						<Pie
							data={chartData}
							dataKey="value"
							nameKey="name"
							cx="50%"
							cy="50%"
							innerRadius="55%"
							outerRadius="85%"
							paddingAngle={1}
							minAngle={2}
							stroke="none"
						>
							{chartData.map((entry, i) => (
								<Cell key={i} fill={entry.fill} />
							))}
						</Pie>
						<Tooltip
							content={({ payload }) => {
								if (!payload || payload.length === 0) return null;
								const entry = payload[0]?.payload as (typeof chartData)[number];
								if (!entry) return null;
								return (
									<div
										style={{
											backgroundColor: "#161b22",
											border: "1px solid rgba(255,255,255,0.1)",
											borderRadius: 8,
											padding: "8px 12px",
										}}
									>
										<p
											style={{
												color: entry.fill,
												fontWeight: 600,
												fontSize: 13,
												textTransform: "capitalize",
											}}
										>
											{entry.name}
										</p>
										<p style={{ color: "#9ca3af", fontSize: 12, marginTop: 2 }}>
											{entry.value.toLocaleString()} visits &middot;{" "}
											{entry.minutes.toLocaleString()} min &middot;{" "}
											{entry.percentage}%
										</p>
									</div>
								);
							}}
						/>
					</PieChart>
				</ResponsiveContainer>
				{/* Center label */}
				<div className="absolute inset-0 flex items-center justify-center pointer-events-none">
					<div className="text-center">
						<p className="text-2xl font-bold text-white">
							{totalVisits.toLocaleString()}
						</p>
						<p className="text-xs text-white/40">visits</p>
					</div>
				</div>
			</div>
		</div>
	);
}
