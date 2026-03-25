import { useMemo, useState } from "react";
import {
	Bar,
	BarChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { CATEGORY_COLORS, type Category, type DomainRankEntry } from "../types";

type SortMode = "visits" | "minutes";

interface DomainRankingProps {
	data: DomainRankEntry[];
}

export function DomainRanking({ data }: DomainRankingProps) {
	const [sortBy, setSortBy] = useState<SortMode>("visits");

	const sorted = useMemo(() => {
		const slice = [...data];
		if (sortBy === "visits") {
			slice.sort((a, b) => b.visit_count - a.visit_count);
		} else {
			slice.sort((a, b) => b.estimated_minutes - a.estimated_minutes);
		}
		return slice.slice(0, 20);
	}, [data, sortBy]);

	if (data.length === 0) {
		return (
			<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6">
				<h3 className="text-sm font-semibold text-white/60 mb-4 tracking-wide uppercase">
					Top Domains
				</h3>
				<p className="text-white/40 text-sm">No data in this range</p>
			</div>
		);
	}

	const chartData = sorted.map((d) => ({
		domain: d.domain.length > 24 ? `${d.domain.slice(0, 22)}...` : d.domain,
		fullDomain: d.domain,
		value: sortBy === "visits" ? d.visit_count : d.estimated_minutes,
		fill:
			CATEGORY_COLORS[d.category as Category] ?? CATEGORY_COLORS.uncategorized,
		visits: d.visit_count,
		minutes: d.estimated_minutes,
	}));

	return (
		<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6">
			<div className="flex items-center justify-between mb-4">
				<h3 className="text-sm font-semibold text-white/60 tracking-wide uppercase">
					Top Domains
				</h3>
				<div className="flex gap-1 bg-white/5 rounded-lg p-0.5">
					<button
						onClick={() => setSortBy("visits")}
						className={`px-3 py-1 text-xs rounded-md transition-colors ${
							sortBy === "visits"
								? "bg-white/10 text-white"
								: "text-white/40 hover:text-white/60"
						}`}
					>
						Visits
					</button>
					<button
						onClick={() => setSortBy("minutes")}
						className={`px-3 py-1 text-xs rounded-md transition-colors ${
							sortBy === "minutes"
								? "bg-white/10 text-white"
								: "text-white/40 hover:text-white/60"
						}`}
					>
						Minutes
					</button>
				</div>
			</div>
			<ResponsiveContainer width="100%" height={sorted.length * 28 + 20}>
				<BarChart
					data={chartData}
					layout="vertical"
					margin={{ top: 0, right: 40, bottom: 0, left: 120 }}
				>
					<XAxis type="number" hide />
					<YAxis
						type="category"
						dataKey="domain"
						width={120}
						tick={{ fill: "#9ca3af", fontSize: 12 }}
						tickLine={false}
						axisLine={false}
					/>
					<Tooltip
						cursor={{ fill: "rgba(255,255,255,0.03)" }}
						contentStyle={{
							backgroundColor: "#161b22",
							border: "1px solid rgba(255,255,255,0.1)",
							borderRadius: 8,
							padding: "8px 12px",
						}}
						labelStyle={{ color: "#fff", fontWeight: 600, marginBottom: 4 }}
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
									<p style={{ color: "#fff", fontWeight: 600, fontSize: 13 }}>
										{entry.fullDomain}
									</p>
									<p style={{ color: "#9ca3af", fontSize: 12, marginTop: 2 }}>
										{entry.visits.toLocaleString()} visits &middot;{" "}
										{entry.minutes.toLocaleString()} min
									</p>
								</div>
							);
						}}
					/>
					<Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={16} />
				</BarChart>
			</ResponsiveContainer>
		</div>
	);
}
