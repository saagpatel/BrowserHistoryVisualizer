import axios from "axios";
import type { AllDatasets, AppStatus } from "../types";

const api = axios.create({
	baseURL: "/api",
});

export async function getStatus(): Promise<AppStatus> {
	const { data } = await api.get<AppStatus>("/status");
	return data;
}

export async function getAll(start: string, end: string): Promise<AllDatasets> {
	const { data } = await api.get<AllDatasets>("/all", {
		params: { start, end },
	});
	return data;
}

export async function postRefresh(): Promise<AppStatus> {
	const { data } = await api.post<AppStatus>("/refresh");
	return data;
}

interface CategorizeResult {
	classified: number;
	cached: number;
	api_calls: number;
	error?: string;
}

export async function postCategorize(): Promise<CategorizeResult> {
	const { data } = await api.post<CategorizeResult>("/categorize");
	return data;
}

export async function getCategories(): Promise<Record<string, string>> {
	const { data } = await api.get<Record<string, string>>("/categories");
	return data;
}

export async function postCategoryOverride(
	domain: string,
	category: string,
): Promise<void> {
	await api.post(`/categories/${encodeURIComponent(domain)}`, { category });
}

export async function postBrowserOverride(
	browser: string,
	path: string,
): Promise<void> {
	await api.post("/settings", { browser, path });
}
