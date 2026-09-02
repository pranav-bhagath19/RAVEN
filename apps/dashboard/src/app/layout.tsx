import type { Metadata } from "next";
import { Mulish, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Shell } from "../components/Shell";

const mulish = Mulish({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
  variable: "--font-sans",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "RAVEN — Autonomous Revenue Recovery Engine",
  description: "Razorpay AI Buildathon Track 03 — Revenue-aware Autonomous Verification & Engine Operations Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${mulish.variable} ${mono.variable}`}>
      <body className={`${mulish.className} bg-[#f4f5f8] text-slate-900 min-h-screen antialiased`}>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
