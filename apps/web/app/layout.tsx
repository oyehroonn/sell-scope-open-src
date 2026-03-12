import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { QueryProvider } from "@/components/providers/query-provider";
import { Toaster } from "@/components/ui/toaster";

export const metadata: Metadata = {
  title: "SellScope - Stock Contributor Intelligence Platform",
  description:
    "The Bloomberg Terminal for Stock Contributors. Stop guessing, start earning with data-driven content decisions.",
  keywords: [
    "adobe stock",
    "stock photography",
    "contributor tools",
    "keyword research",
    "stock analytics",
    "opportunity scoring",
  ],
  authors: [{ name: "SellScope" }],
  openGraph: {
    title: "SellScope - Stock Contributor Intelligence Platform",
    description:
      "Transform stock contribution from guesswork into data-driven creation",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${GeistSans.variable} ${GeistMono.variable} font-sans antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>{children}</QueryProvider>
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
