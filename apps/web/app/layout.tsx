import "./globals.css";
import { AppShell } from "@/components/AppShell";
import { I18nProvider } from "@/lib/i18n";
import { ThemeProvider } from "@/components/ThemeProvider";
import { ToastProvider } from "@/lib/toast";

export const metadata = {
  title: "China-VNE | Video Localization",
  description: "Chinese → Vietnamese AI video localization platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <ToastProvider>
            <I18nProvider>
              <AppShell>{children}</AppShell>
            </I18nProvider>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
