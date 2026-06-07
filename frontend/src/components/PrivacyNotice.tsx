import { useState } from "react";

const STORAGE_KEY = "bhv-privacy-dismissed";

export function PrivacyNotice() {
	const [visible, setVisible] = useState(
		() => !localStorage.getItem(STORAGE_KEY),
	);

	if (!visible) return null;

	const dismiss = () => {
		localStorage.setItem(STORAGE_KEY, "1");
		setVisible(false);
	};

	return (
		<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
			<div className="bg-[#0d1117] border border-white/10 rounded-2xl p-8 max-w-md mx-4 shadow-2xl">
				<h2 className="text-lg font-bold text-white mb-3">
					Your data stays local
				</h2>
				<p className="text-sm text-white/60 leading-relaxed mb-2">
					BHV reads your browser history from local SQLite databases and runs
					entirely on <code className="text-cyan-400">127.0.0.1</code>.
				</p>
				<ul className="text-sm text-white/50 space-y-1 mb-6 list-disc list-inside">
					<li>No cloud services, no telemetry, no external requests</li>
					<li>All data stays on this machine</li>
					<li>Browser databases are opened read-only</li>
					<li>
						Optional AI categorization uses your Anthropic API key (domain names
						only — no URLs, titles, or visit data sent)
					</li>
				</ul>
				<button
					onClick={dismiss}
					className="w-full px-4 py-2.5 text-sm font-medium rounded-lg bg-white/10 text-white hover:bg-white/15 transition-colors"
				>
					Got it
				</button>
			</div>
		</div>
	);
}
