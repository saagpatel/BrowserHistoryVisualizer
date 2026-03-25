export interface HeatmapDay {
	date: string;
	count: number;
	intensity: 0 | 1 | 2 | 3 | 4;
}

export interface TopicSlice {
	category: string;
	visits: number;
	estimated_minutes: number;
	percentage: number;
}

export interface DomainRankEntry {
	domain: string;
	category: string;
	visit_count: number;
	estimated_minutes: number;
}

export interface ProductivityPoint {
	hour: number;
	focus_minutes: number;
	distraction_minutes: number;
	ratio: number;
}

export interface RabbitHoleNode {
	id: string;
	domain: string;
	title: string;
	category: string;
}

export interface RabbitHoleSession {
	session_id: string;
	start_time: number;
	duration_minutes: number;
	visit_count: number;
	dominant_topic: string;
	nodes: RabbitHoleNode[];
	edges: [string, string][];
}

export interface DetectedBrowser {
	name: string;
	path: string;
	visit_count: number;
	detected: boolean;
	manual_override: boolean;
}

export interface AppStatus {
	browsers: DetectedBrowser[];
	total_visits: number;
	date_range_available: [string, string];
	last_refreshed: number | null;
}

export interface AllDatasets {
	status: AppStatus;
	heatmap: HeatmapDay[];
	topics: TopicSlice[];
	domains: DomainRankEntry[];
	productivity: ProductivityPoint[];
	rabbit_holes: RabbitHoleSession[];
}

export type DateRange = { start: string; end: string };

export type Category =
	| "work"
	| "research"
	| "social"
	| "news"
	| "entertainment"
	| "shopping"
	| "devtools"
	| "uncategorized";

export const CATEGORY_COLORS: Record<Category, string> = {
	work: "#3b82f6",
	research: "#8b5cf6",
	social: "#ec4899",
	news: "#f59e0b",
	entertainment: "#ef4444",
	shopping: "#10b981",
	devtools: "#06b6d4",
	uncategorized: "#6b7280",
};
