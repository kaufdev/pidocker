import { randomBytes } from "node:crypto";
import { mkdir, readdir, rename, rm, writeFile } from "node:fs/promises";
import { basename, dirname, extname, join, resolve } from "node:path";
import { SessionManager, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

const SESSIONS_ROOT = "/home/pi/.pi/agent/instance-sessions";
const ALIAS_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$/;
const HEX_PATTERN = /^[0-9a-f]+$/;

type ListedSession = Awaited<ReturnType<typeof SessionManager.listAll>>[number];

function requiredEnv(name: string): string {
	const value = process.env[name];
	if (!value) throw new Error(`${name} is not set`);
	return value;
}

function compactText(text: string): string {
	const normalized = text.replace(/\s+/g, " ").trim() || "(no messages)";
	return normalized.length > 42 ? `${normalized.slice(0, 41)}…` : normalized;
}

function sessionLabel(session: ListedSession, instanceSuffix: string): string {
	const modified = session.modified.toISOString().slice(0, 16).replace("T", " ");
	const title = compactText(session.name || session.firstMessage);
	return `${modified}  ${title}  ${session.id.slice(0, 8)}  @${instanceSuffix}`;
}

export default function resumeRepoExtension(pi: ExtensionAPI) {
	pi.registerCommand("resume-repo", {
		description: "Resume a session from another repository instance",
		handler: async (_args, ctx) => {
			try {
				const alias = requiredEnv("PIDOCKER_REPO_ALIAS");
				const launchId = requiredEnv("PIDOCKER_RESUME_LAUNCH_ID");
				const requestDir = requiredEnv("PIDOCKER_RESUME_REQUEST_DIR");

				if (!ALIAS_PATTERN.test(alias)) throw new Error("PIDOCKER_REPO_ALIAS is invalid");
				if (!HEX_PATTERN.test(launchId)) throw new Error("PIDOCKER_RESUME_LAUNCH_ID must be lowercase hex");

				const prefix = `${alias}-`;
				const entries = await readdir(SESSIONS_ROOT, { withFileTypes: true });
				const instances = entries.filter((entry) => {
					const suffix = entry.name.slice(prefix.length);
					return entry.isDirectory() && entry.name.startsWith(prefix) && /^[0-9a-f]{12}$/.test(suffix);
				});

				const found: Array<{ session: ListedSession; instanceId: string; instanceDir: string }> = [];
				for (const instance of instances) {
					const instanceDir = join(SESSIONS_ROOT, instance.name);
					try {
						const sessions = await SessionManager.listAll(instanceDir);
						found.push(...sessions.map((session) => ({ session, instanceId: instance.name, instanceDir })));
					} catch {
						// A broken instance must not hide sessions from the others.
					}
				}

				found.sort((a, b) => b.session.modified.getTime() - a.session.modified.getTime());
				const labels = new Set<string>();
				const choices = found.slice(0, 30).map((item) => {
					const base = sessionLabel(item.session, item.instanceId.slice(-12));
					let label = base;
					let duplicate = 2;
					while (labels.has(label)) label = `${base} · ${duplicate++}`;
					labels.add(label);
					return { ...item, label };
				});

				if (choices.length === 0) {
					ctx.ui.notify("No repository sessions found", "info");
					return;
				}

				const selectedLabel = await ctx.ui.select(
					"Resume repository session",
					choices.map((choice) => choice.label),
				);
				if (!selectedLabel) return;

				const selected = choices.find((choice) => choice.label === selectedLabel)!;
				const sessionPath = resolve(selected.session.path);
				if (dirname(sessionPath) !== selected.instanceDir || extname(sessionPath) !== ".jsonl") {
					throw new Error("Selected session path is invalid");
				}

				await mkdir(requestDir, { recursive: true, mode: 0o700 });
				const requestPath = join(requestDir, `${launchId}.request`);
				const tempPath = join(requestDir, `.${launchId}.${process.pid}.${randomBytes(6).toString("hex")}.tmp`);
				try {
					await writeFile(tempPath, `${selected.instanceId}\n${basename(sessionPath)}\n`, {
						flag: "wx",
						mode: 0o600,
					});
					await rename(tempPath, requestPath);
				} catch (error) {
					await rm(tempPath, { force: true }).catch(() => undefined);
					throw error;
				}

				ctx.shutdown();
			} catch (error) {
				const message = error instanceof Error ? error.message : String(error);
				ctx.ui.notify(`Unable to resume repository session: ${message}`, "error");
			}
		},
	});
}
