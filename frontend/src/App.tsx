import { useState } from "react";
import { DateRangePicker } from "./components/DateRangePicker";
import { DomainRanking } from "./components/DomainRanking";
import { HeatmapCalendar } from "./components/HeatmapCalendar";
import { PrivacyNotice } from "./components/PrivacyNotice";
import { ProductivityCurve } from "./components/ProductivityCurve";
import { RabbitHoleGraph } from "./components/RabbitHoleGraph";
import { Settings } from "./components/Settings";
import { TopicDonut } from "./components/TopicDonut";
import { useAnalytics } from "./hooks/useAnalytics";
import type { DateRange } from "./types";

type View = "dashboard" | "settings";

function defaultDateRange(): DateRange {
	const end = new Date();
	const start = new Date();
	start.setDate(start.getDate() - 30);
	return {
		start: start.toISOString().slice(0, 10),
		end: end.toISOString().slice(0, 10),
	};
}

function LoadingSkeleton() {
	return (
		<div className="space-y-6 animate-pulse">
			<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6 h-[180px]" />
			<div className="grid grid-cols-5 gap-6">
				<div className="col-span-2 rounded-xl bg-[#0d1117] border border-white/10 p-6 h-[340px]" />
				<div className="col-span-3 rounded-xl bg-[#0d1117] border border-white/10 p-6 h-[340px]" />
			</div>
			<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6 h-[600px]" />
		</div>
	);
}

function ErrorMessage({ message }: { message: string }) {
	return (
		<div className="rounded-xl bg-red-950/30 border border-red-500/20 p-6">
			<p className="text-red-400 text-sm font-medium">Failed to load data</p>
			<p className="text-red-400/60 text-xs mt-1">{message}</p>
		</div>
	);
}

export default function App() {
	const [view, setView] = useState<View>("dashboard");
	const [dateRange, setDateRange] = useState<DateRange>(defaultDateRange);
	const { data, loading, error, refetch } = useAnalytics(dateRange);

	return (
		<div className="min-h-screen bg-[#010409] text-white">
			<PrivacyNotice />
			<div className="flex">
				{/* Sidebar */}
				<nav className="w-52 min-h-screen bg-[#0d1117] border-r border-white/10 p-4 flex flex-col gap-1 sticky top-0 h-screen">
					<div className="px-3 py-2 mb-4">
						<h1 className="text-base font-bold tracking-tight">BHV</h1>
						<p className="text-[11px] text-white/30 mt-0.5">
							Browser History Visualizer
						</p>
					</div>
					<button
						onClick={() => setView("dashboard")}
						className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg text-left transition-colors ${
							view === "dashboard"
								? "bg-white/5 text-white"
								: "text-white/40 hover:text-white/60"
						}`}
					>
						<span
							className={`w-1.5 h-1.5 rounded-full ${view === "dashboard" ? "bg-emerald-400" : "bg-white/20"}`}
						/>
						Dashboard
					</button>
					<button
						onClick={() => setView("settings")}
						className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg text-left transition-colors ${
							view === "settings"
								? "bg-white/5 text-white"
								: "text-white/40 hover:text-white/60"
						}`}
					>
						<span
							className={`w-1.5 h-1.5 rounded-full ${view === "settings" ? "bg-emerald-400" : "bg-white/20"}`}
						/>
						Settings
					</button>

					{/* Status footer */}
					{data && (
						<div className="mt-auto pt-4 border-t border-white/5">
							<p className="text-[11px] text-white/20 px-3">
								{data.status.total_visits.toLocaleString()} visits
							</p>
							<p className="text-[11px] text-white/20 px-3">
								{data.status.browsers.filter((b) => b.detected).length}{" "}
								browser(s)
							</p>
							{data.status.last_refreshed && (
								<p className="text-[11px] text-white/20 px-3">
									Updated{" "}
									{new Date(
										data.status.last_refreshed * 1000,
									).toLocaleDateString()}
								</p>
							)}
						</div>
					)}
				</nav>

				{/* Main content */}
				<main className="flex-1 p-8 max-w-5xl">
					{view === "dashboard" && (
						<>
							<div className="flex items-center justify-between mb-8">
								<h2 className="text-xl font-bold tracking-tight">Dashboard</h2>
								{data && (
									<DateRangePicker
										value={dateRange}
										onChange={setDateRange}
										availableRange={data.status.date_range_available}
									/>
								)}
							</div>

							{loading && <LoadingSkeleton />}
							{error && <ErrorMessage message={error} />}

							{data && (
								<div className="space-y-6">
									<HeatmapCalendar data={data.heatmap} />
									<div className="grid grid-cols-5 gap-6">
										<div className="col-span-2">
											<TopicDonut data={data.topics} />
										</div>
										<div className="col-span-3">
											<ProductivityCurve data={data.productivity} />
										</div>
									</div>
									<DomainRanking data={data.domains} />
									<RabbitHoleGraph data={data.rabbit_holes} />
								</div>
							)}
						</>
					)}

					{view === "settings" && (
						<>
							<div className="mb-8">
								<h2 className="text-xl font-bold tracking-tight">Settings</h2>
							</div>
							{data && (
								<Settings status={data.status} onRefreshComplete={refetch} />
							)}
						</>
					)}
				</main>
			</div>
		</div>
	);
}
