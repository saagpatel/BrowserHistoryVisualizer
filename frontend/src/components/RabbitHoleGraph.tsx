import * as d3 from "d3";
import { useEffect, useMemo, useRef, useState } from "react";
import {
	CATEGORY_COLORS,
	type Category,
	type RabbitHoleSession,
} from "../types";

interface RabbitHoleGraphProps {
	data: RabbitHoleSession[];
}

interface SimNode extends d3.SimulationNodeDatum {
	id: string;
	domain: string;
	title: string;
	category: string;
	degree: number;
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
	source: string | SimNode;
	target: string | SimNode;
}

function buildGraphData(session: RabbitHoleSession) {
	// Count degree per node
	const degreeMap = new Map<string, number>();
	for (const [src, tgt] of session.edges) {
		degreeMap.set(src, (degreeMap.get(src) ?? 0) + 1);
		degreeMap.set(tgt, (degreeMap.get(tgt) ?? 0) + 1);
	}

	const nodes: SimNode[] = session.nodes.map((n) => ({
		id: n.id,
		domain: n.domain,
		title: n.title,
		category: n.category,
		degree: degreeMap.get(n.id) ?? 1,
	}));

	const nodeIds = new Set(nodes.map((n) => n.id));
	const links: SimLink[] = session.edges
		.filter(([src, tgt]) => nodeIds.has(src) && nodeIds.has(tgt))
		.map(([source, target]) => ({ source, target }));

	return { nodes, links };
}

export function RabbitHoleGraph({ data }: RabbitHoleGraphProps) {
	const svgRef = useRef<SVGSVGElement>(null);
	const containerRef = useRef<HTMLDivElement>(null);
	const [selectedIdx, setSelectedIdx] = useState(0);

	// Limit to top 20 sessions by duration
	const sessions = useMemo(() => data.slice(0, 20), [data]);
	const session = sessions[selectedIdx] ?? null;

	useEffect(() => {
		if (!svgRef.current || !session) return;

		const svg = d3.select(svgRef.current);
		svg.selectAll("*").remove();

		const width = svgRef.current.clientWidth || 800;
		const height = 400;
		svg.attr("width", width).attr("height", height);

		const { nodes, links } = buildGraphData(session);
		if (nodes.length === 0) return;

		// Scale node radius by degree
		const maxDegree = Math.max(...nodes.map((n) => n.degree));
		const radiusScale = d3
			.scaleLinear()
			.domain([1, Math.max(maxDegree, 2)])
			.range([6, 18]);

		const simulation = d3
			.forceSimulation<SimNode>(nodes)
			.force(
				"link",
				d3
					.forceLink<SimNode, SimLink>(links)
					.id((d) => d.id)
					.distance(80),
			)
			.force("charge", d3.forceManyBody().strength(-120))
			.force("center", d3.forceCenter(width / 2, height / 2))
			.force(
				"collision",
				d3.forceCollide<SimNode>().radius((d) => radiusScale(d.degree) + 2),
			);

		// Edges
		const link = svg
			.append("g")
			.selectAll("line")
			.data(links)
			.join("line")
			.attr("stroke", "rgba(255,255,255,0.08)")
			.attr("stroke-width", 1);

		// Tooltip
		const tooltip = d3
			.select("body")
			.append("div")
			.attr("class", "bhv-tooltip")
			.style("position", "fixed")
			.style("pointer-events", "none")
			.style("background", "#161b22")
			.style("border", "1px solid rgba(255,255,255,0.1)")
			.style("border-radius", "8px")
			.style("padding", "6px 10px")
			.style("font-size", "12px")
			.style("color", "#fff")
			.style("z-index", "9999")
			.style("opacity", "0");

		// Nodes
		const node = svg
			.append("g")
			.selectAll<SVGCircleElement, SimNode>("circle")
			.data(nodes)
			.join("circle")
			.attr("r", (d) => radiusScale(d.degree))
			.attr(
				"fill",
				(d) =>
					CATEGORY_COLORS[d.category as Category] ??
					CATEGORY_COLORS.uncategorized,
			)
			.attr("stroke", "rgba(255,255,255,0.15)")
			.attr("stroke-width", 1)
			.style("cursor", "grab")
			.on("mouseover", (_event, d) => {
				tooltip
					.style("opacity", "1")
					.html(
						`<strong>${d.domain}</strong><br/><span style="color:#9ca3af">${d.title.length > 60 ? d.title.slice(0, 57) + "..." : d.title}</span>`,
					);
			})
			.on("mousemove", (event) => {
				tooltip
					.style("left", event.clientX + 12 + "px")
					.style("top", event.clientY - 10 + "px");
			})
			.on("mouseout", () => {
				tooltip.style("opacity", "0");
			});

		// Drag
		const drag = d3
			.drag<SVGCircleElement, SimNode>()
			.on("start", (event, d) => {
				if (!event.active) simulation.alphaTarget(0.3).restart();
				d.fx = d.x;
				d.fy = d.y;
			})
			.on("drag", (event, d) => {
				d.fx = event.x;
				d.fy = event.y;
			})
			.on("end", (event, d) => {
				if (!event.active) simulation.alphaTarget(0);
				d.fx = null;
				d.fy = null;
			});

		node.call(drag);

		simulation.on("tick", () => {
			link
				.attr("x1", (d) => (d.source as SimNode).x ?? 0)
				.attr("y1", (d) => (d.source as SimNode).y ?? 0)
				.attr("x2", (d) => (d.target as SimNode).x ?? 0)
				.attr("y2", (d) => (d.target as SimNode).y ?? 0);
			node.attr("cx", (d) => d.x ?? 0).attr("cy", (d) => d.y ?? 0);
		});

		return () => {
			simulation.stop();
			tooltip.remove();
		};
	}, [session]);

	if (sessions.length === 0) {
		return (
			<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6">
				<h3 className="text-sm font-semibold text-white/60 mb-4 tracking-wide uppercase">
					Rabbit Holes
				</h3>
				<p className="text-white/40 text-sm">No rabbit holes in this range</p>
			</div>
		);
	}

	return (
		<div className="rounded-xl bg-[#0d1117] border border-white/10 p-6">
			<div className="flex items-center justify-between mb-4">
				<h3 className="text-sm font-semibold text-white/60 tracking-wide uppercase">
					Rabbit Holes
				</h3>
				{sessions.length > 1 && (
					<select
						value={selectedIdx}
						onChange={(e) => setSelectedIdx(Number(e.target.value))}
						className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none [color-scheme:dark]"
					>
						{sessions.map((s, i) => (
							<option key={s.session_id} value={i}>
								{s.dominant_topic} — {s.visit_count} visits,{" "}
								{s.duration_minutes}m
							</option>
						))}
					</select>
				)}
			</div>
			{session && (
				<div className="text-xs text-white/30 mb-2">
					{session.nodes.length} pages, {session.edges.length} links,{" "}
					{session.duration_minutes} min
				</div>
			)}
			<div ref={containerRef} className="w-full">
				<svg ref={svgRef} className="w-full" style={{ height: 400 }} />
			</div>
		</div>
	);
}
