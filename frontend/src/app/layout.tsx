import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ThoughtFocus KB Portal",
  description: "Department knowledge base portal - upload, process, and search documents",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen">{children}</body>
    </html>
  );
}
