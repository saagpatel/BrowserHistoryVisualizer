import { useCallback, useEffect, useState } from "react";
import { getAll } from "../api/client";
import type { AllDatasets, DateRange } from "../types";

function defaultDateRange(): DateRange {
	const end = new Date();
	const start = new Date();
	start.setDate(start.getDate() - 30);
	return {
		start: start.toISOString().slice(0, 10),
		end: end.toISOString().slice(0, 10),
	};
}

export function useAnalytics(dateRange?: DateRange) {
	const range = dateRange ?? defaultDateRange();
	const [data, setData] = useState<AllDatasets | null>(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	const fetchData = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const result = await getAll(range.start, range.end);
			setData(result);
		} catch (err) {
			const message =
				err instanceof Error ? err.message : "Failed to load data";
			setError(message);
		} finally {
			setLoading(false);
		}
	}, [range.start, range.end]);

	useEffect(() => {
		fetchData();
	}, [fetchData]);

	return { data, loading, error, refetch: fetchData };
}
