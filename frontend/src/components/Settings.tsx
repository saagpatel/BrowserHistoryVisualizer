import { useState } from "react";
import {
	postBrowserOverride,
	postCategorize,
	postCategoryOverride,
	postRefresh,
} from "../api/client";
import type { AppStatus, Category } from "../types";

const CATEGORIES: Category[] = [
	"work",
	"research",
	"social",
	"news",
	"entertainment",
	"shopping",
	"devtools",
	"uncategorized",
];

interface SettingsProps {
	status: AppStatus;
	onRefreshComplete: () => void;
}

export function Settings({ status, onRefreshComplete }: SettingsProps) {
	const [refreshing, setRefreshing] = useState(false);
	const [categorizing, setCategorizing] = useState(false);
	const [catResult, setCatResult] = useState<string | null>(null);

	// Category override form
	const [overrideDomain, setOverrideDomain] = useState("");
	const [overrideCategory, setOverrideCategory] = useState<Category>("work");
	const [overrideMsg, setOverrideMsg] = useState<string | null>(null);

	// Browser path override
	const [editingBrowser, setEditingBrowser] = useState<string | null>(null);
	const [browserPath, setBrowserPath] = useState("");

	const handleRefresh = async () => {
		setRefreshing(true);
		try {
			await postRefresh();
			onRefreshComplete();
		} catch (err) {
			console.error("Refresh failed:", err);
		} finally {
			setRefreshing(false);
		}
	};

	const handleCategorize = async () => {
		setCategorizing(true);
		setCatResult(null);
		try {
			const result = await postCategorize();
			if (result.error) {
				setCatResult(result.error);
			} else {
				setCatResult(
					`Classified ${result.classified} domains in ${result.api_calls} API call(s)`,
				);
			}
		} catch {
			setCatResult("Categorization failed");
		} finally {
			setCategorizing(false);
		}
	};

	const handleOverride = async () => {
		if (!overrideDomain.trim()) return;
		try {
			await postCategoryOverride(overrideDomain.trim(), overrideCategory);
			setOverrideMsg(`${overrideDomain} set to ${overrideCategory}`);
			setOverrideDomain("");
		} catch {
			setOverrideMsg("Override failed");
		}
	};

	const handleBrowserOverride = async (browser: string) => {
		if (!browserPath.trim()) return;
		try {
			await postBrowserOverride(browser, browserPath.trim());
			setEditingBrowser(null);
			setBrowserPath("");
		} catch {
			console.error("Browser override failed");
		}
	};

	return (
		<div className="space-y-6">
			{/* Browsers */}
			<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6">
				<h3 className="text-sm font-semibold text-white/60 mb-4 tracking-wide uppercase">
					Detected Browsers
				</h3>
				<div className="space-y-3">
					{status.browsers.map((browser) => (
						<div key={browser.path}>
							<div className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
								<div className="flex items-center gap-3">
									<span
										className={`w-2 h-2 rounded-full ${
											browser.detected ? "bg-emerald-400" : "bg-red-400"
										}`}
									/>
									<div>
										<p className="text-sm text-white capitalize">
											{browser.name}
										</p>
										<p className="text-xs text-white/30 font-mono truncate max-w-md">
											{browser.path}
										</p>
									</div>
								</div>
								<div className="flex items-center gap-4">
									<span className="text-xs text-white/40">
										{browser.visit_count >= 0
											? `${browser.visit_count.toLocaleString()} visits`
											: "locked"}
									</span>
									<button
										onClick={() => {
											setEditingBrowser(
												editingBrowser === browser.name ? null : browser.name,
											);
											setBrowserPath(browser.path);
										}}
										className="px-3 py-1 text-xs rounded-md bg-white/5 text-white/60 hover:text-white hover:bg-white/10 transition-colors"
									>
										Override
									</button>
								</div>
							</div>
							{editingBrowser === browser.name && (
								<div className="flex items-center gap-2 py-2 pl-8">
									<input
										type="text"
										value={browserPath}
										onChange={(e) => setBrowserPath(e.target.value)}
										placeholder="Custom path to History file"
										className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-white/20"
									/>
									<button
										onClick={() => handleBrowserOverride(browser.name)}
										className="px-3 py-1.5 text-xs rounded-lg bg-cyan-600/20 text-cyan-400 hover:bg-cyan-600/30 transition-colors"
									>
										Save
									</button>
								</div>
							)}
						</div>
					))}
				</div>
			</div>

			{/* Category Overrides */}
			<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6">
				<h3 className="text-sm font-semibold text-white/60 mb-4 tracking-wide uppercase">
					Category Overrides
				</h3>
				<div className="flex items-center gap-2">
					<input
						type="text"
						value={overrideDomain}
						onChange={(e) => setOverrideDomain(e.target.value)}
						placeholder="domain.com"
						className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-white/20 w-48"
					/>
					<select
						value={overrideCategory}
						onChange={(e) => setOverrideCategory(e.target.value as Category)}
						className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none [color-scheme:dark]"
					>
						{CATEGORIES.map((c) => (
							<option key={c} value={c}>
								{c}
							</option>
						))}
					</select>
					<button
						onClick={handleOverride}
						className="px-4 py-1.5 text-sm rounded-lg bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-colors"
					>
						Save
					</button>
				</div>
				{overrideMsg && (
					<p className="text-xs text-white/40 mt-2">{overrideMsg}</p>
				)}
			</div>

			{/* Data */}
			<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6">
				<h3 className="text-sm font-semibold text-white/60 mb-4 tracking-wide uppercase">
					Data
				</h3>
				<div className="flex items-center gap-4 flex-wrap">
					<button
						onClick={handleRefresh}
						disabled={refreshing}
						className="px-4 py-2 text-sm rounded-lg bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-colors disabled:opacity-50"
					>
						{refreshing ? "Refreshing..." : "Refresh Data"}
					</button>
					<button
						onClick={handleCategorize}
						disabled={categorizing}
						className="px-4 py-2 text-sm rounded-lg bg-cyan-600/20 border border-cyan-600/30 text-cyan-400 hover:bg-cyan-600/30 transition-colors disabled:opacity-50"
					>
						{categorizing ? "Categorizing..." : "Run AI Categorization"}
					</button>
					{status.last_refreshed && (
						<span className="text-xs text-white/30">
							Last updated:{" "}
							{new Date(status.last_refreshed * 1000).toLocaleString()}
						</span>
					)}
				</div>
				{catResult && <p className="text-xs text-white/40 mt-2">{catResult}</p>}
			</div>
		</div>
	);
}
