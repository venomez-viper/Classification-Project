import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";

export const metadata: Metadata = {
  title: "GECS Classification Engine | MGT 599 Capstone · Group 4",
  description:
    "AI-powered Morningstar GECS industry and subindustry classification using breezeml, TF-IDF, and Linear SVM. Built by Group 4 for the MGT 599 Capstone.",
  keywords: ["GECS", "Morningstar", "Machine Learning", "Classification", "breezeml", "NLP", "TF-IDF"],
};

// ── Haptic ripple + vibration on every button click ───────────────────────────
function HapticScript() {
  const script = `
    (function() {
      document.addEventListener('click', function(e) {
        var btn = e.target.closest('button, [role="button"]');
        if (!btn || btn.disabled) return;

        // Device vibration (mobile)
        if (navigator.vibrate) navigator.vibrate(8);

        // Ripple element
        var r = document.createElement('span');
        r.className = 'haptic-ripple';
        var rect = btn.getBoundingClientRect();
        r.style.left = (e.clientX - rect.left) + 'px';
        r.style.top  = (e.clientY - rect.top)  + 'px';
        btn.appendChild(r);
        setTimeout(function() { r.remove(); }, 450);
      }, { passive: true });
    })();
  `;
  return <script dangerouslySetInnerHTML={{ __html: script }} />;
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" style={{ colorScheme: "dark" }}>
      <body className={`${GeistSans.variable} ${GeistMono.variable} antialiased`}>
        <HapticScript />
        {children}
      </body>
    </html>
  );
}

