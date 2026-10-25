import type { Metadata } from "next";
import "@fontsource-variable/manrope";
import "./globals.css";
export const metadata: Metadata = {
  title: "AI Auditor — follow the evidence",
  description:
    "Review AI-generated claims against your reference documents, with transparent evidence and corrective retrieval.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
