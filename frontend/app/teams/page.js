import fs from "node:fs";
import path from "node:path";
import Script from "next/script";
export default function TeamsPage() {
  const html = fs.readFileSync(path.join(process.cwd(), "legacy", "index.html"), "utf8");
  const body = html.match(/<body>([\s\S]*?)<script src=/)?.[1] || "";
  return <><div dangerouslySetInnerHTML={{ __html: body }} /><Script src="/teams-assets/teams.js?v=20260918-34" strategy="afterInteractive" /></>;
}
