/**
 * Header — Application title bar.
 *
 * Simplified: session info and controls moved to LeftSidebar.
 * Header now only shows app name and subtitle.
 */

import { APP_CONFIG } from "../utils/constants";

export default function Header() {
  return (
    <header className="header">
      <div>
        <p className="eyebrow">{APP_CONFIG.APP_SUBTITLE}</p>
        <h1>{APP_CONFIG.APP_NAME}</h1>
      </div>
    </header>
  );
}